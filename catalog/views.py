import json
from decimal import Decimal, InvalidOperation

from django.db.models import Count, Max, Min, Prefetch
from django.shortcuts import get_object_or_404
from django.utils.translation import get_language
from django.views.generic import DetailView, ListView, TemplateView

from cart.services import WishlistService
from pages.forms_extra import PhotoPickForm
from pages.i18n_lib import plural_goods, tr
from pages.models_extra import BlogPost
from pages.picker_defaults import (
    get_home_doors,
    get_picker_filters,
    get_picker_options_json,
)
from pages.popular_products import get_home_popular
from pages.views_extra import _form_with_key

from .listing_scope import apply_listing_scope, category_nav_chips, listing_scope
from .pagination import ClampPageMixin
from .chrome_cms import catalog_chrome
from .models import Attribute, AttributeValue, Category, Product, ProductImage
from .measure_guide import resolve_measure
from .product_html import product_description_html
from .product_meta import review_summary
from .reviews import INITIAL_VISIBLE, ReviewForm
from .db_compat import published_reviews_for
from .product_specs import product_brand, product_spec_rows
from .product_variants import build_variant_context
from .search import filter_queryset_by_query

SORT_MAP = {
    'default': ('catalog_order', 'name'),
    'cheap': ('price', 'catalog_order'),
    'expensive': ('-price', 'catalog_order'),
    'new': ('-is_new', 'catalog_order'),
    'rating': ('-rating', 'catalog_order'),
}

PAGE_SIZE = 12
FILTER_OPEN_COUNT = 3

HOME_CATEGORY_SUBS = [
    'Врізні, накладні, електромеханічні',
    'Секретність та надійність',
    'Ручки, петлі, завіси і розетки',
    'Захист від злому',
    'Для комфортного закривання',
    'Кодові замки, домофони, СКУД',
]

HOME_CATEGORY_IMAGES = [
    'img/v2/p2_8.webp',
    'img/v2/p2_9.webp',
    'img/v2/p2_10.webp',
    'img/v2/p2_11.webp',
    'img/v2/p2_12.webp',
    'img/v2/p2_13.webp',
]

BLOG_FALLBACK_COVERS = [
    'img/v2/article1.webp',
    'img/v2/p2_34.webp',
    'img/v2/p2_35.webp',
    'img/v2/p2_36.webp',
]

class HomeView(TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cats = Category.objects.filter(
            is_active=True, show_on_home=True, parent__isnull=True
        ).order_by(
            'sort_order', 'name'
        )
        popular = get_home_popular()
        hits = popular['hits']
        news = popular['news']
        sales = popular['sales']

        from pages.home_cms import build_home_cms

        cms = build_home_cms(self.request)
        lang = cms.get('cms_lang') or 'ua'
        door_types = get_home_doors(lang)
        picker_filters = get_picker_filters(lang)
        picker_options = get_picker_options_json(lang)
        blog_posts = BlogPost.objects.filter(is_published=True).order_by(
            'sort_order', '-created_at'
        )[:4]
        cat_list = list(cats)
        category_cards = []
        for i, cat in enumerate(cat_list):
            sub = cat.card_subtitle(lang)
            if not sub and i < len(HOME_CATEGORY_SUBS):
                sub = tr(HOME_CATEGORY_SUBS[i])
            category_cards.append(
                {
                    'category': cat,
                    'title': cat.card_name(lang),
                    'sub': sub,
                    'fallback_image': HOME_CATEGORY_IMAGES[i % len(HOME_CATEGORY_IMAGES)],
                }
            )

        ctx.update(
            {
                'categories': cats,
                'category_cards': category_cards,
                'blog_fallback_covers': BLOG_FALLBACK_COVERS,
                'hits': hits,
                'news': news,
                'sales': sales,
                'door_types': door_types,
                'picker_filters': picker_filters,
                'blog_posts': blog_posts,
                'photo_pick_form': _form_with_key(self.request, PhotoPickForm, 'photo_pick'),
                'picker_options': picker_options,
            }
        )
        ctx.update(cms)
        return ctx


class CatalogView(ClampPageMixin, ListView):
    model = Product
    template_name = 'catalog/catalog.html'
    context_object_name = 'products'
    paginate_by = PAGE_SIZE

    def get_paginate_by(self, queryset):
        try:
            limit = int(self.request.GET.get('limit', PAGE_SIZE))
        except (TypeError, ValueError):
            limit = PAGE_SIZE
        return max(PAGE_SIZE, min(limit, 240))

    def get_queryset(self):
        qs = self._catalog_products().prefetch_related('images', 'attributes')
        self.category = None
        slug = self.kwargs.get('slug')
        if slug:
            self.category = get_object_or_404(Category, slug=slug, is_active=True)
            qs = apply_listing_scope(qs, listing_scope(self.category))

        q = self.request.GET.get('q', '').strip()
        self._search_q = q

        sku = self.request.GET.get('sku', '').strip()
        if sku:
            qs = qs.filter(sku__icontains=sku)

        qs = self._apply_attr_filters(qs)

        price_min = self._decimal(self.request.GET.get('price_min'))
        price_max = self._decimal(self.request.GET.get('price_max'))
        if price_min is not None:
            qs = qs.filter(price__gte=price_min)
        if price_max is not None:
            qs = qs.filter(price__lte=price_max)

        # Fuzzy/кирилиця після інших фільтрів; порядок релевантності, якщо немає явного sort.
        sort = self.request.GET.get('sort', 'default')
        if q:
            qs = filter_queryset_by_query(qs, q)
            if sort and sort != 'default':
                ordering = SORT_MAP.get(sort, SORT_MAP['default'])
                return qs.order_by(*ordering).distinct()
            return qs.distinct()

        ordering = SORT_MAP.get(sort, SORT_MAP['default'])
        return qs.distinct().order_by(*ordering)

    def _decimal(self, raw):
        if raw in (None, ''):
            return None
        try:
            return Decimal(str(raw).replace(',', '.'))
        except (InvalidOperation, ValueError):
            return None

    def _catalog_products(self):
        """Товари вітрини каталогу (як PRODUCTS у Catalog.dc.html): без HOME-* і без PDP/lock (order≥500)."""
        return Product.objects.filter(is_active=True, catalog_order__lt=500).exclude(
            sku__startswith='HOME-'
        )

    def _filterable_attrs(self):
        cached = getattr(self, '_filterable_attrs_cache', None)
        if cached is None:
            self._filterable_attrs_cache = list(
                Attribute.objects.filter(filterable=True)
                .prefetch_related('values')
                .order_by('sort_order', 'name')
            )
            cached = self._filterable_attrs_cache
        return cached

    def _apply_attr_filters(self, qs, skip_key=None):
        for attr in self._filterable_attrs():
            if attr.slug == skip_key:
                continue
            values = self.request.GET.getlist(attr.slug)
            if values:
                qs = qs.filter(
                    attributes__slug__in=values,
                    attributes__attribute__slug=attr.slug,
                )
        return qs

    def _base_qs(self):
        base = self._catalog_products()
        if self.category:
            base = apply_listing_scope(base, listing_scope(self.category))
        return base

    def _filter_counts(self, base, skip_key=None):
        """Лічильники опцій з урахуванням інших активних фільтрів."""
        qs = self._apply_attr_filters(base, skip_key=skip_key)
        sku = self.request.GET.get('sku', '').strip()
        if sku:
            qs = qs.filter(sku__icontains=sku)
        price_min = self._decimal(self.request.GET.get('price_min'))
        price_max = self._decimal(self.request.GET.get('price_max'))
        if price_min is not None:
            qs = qs.filter(price__gte=price_min)
        if price_max is not None:
            qs = qs.filter(price__lte=price_max)
        # без .distinct() тут — він ламає подальший values()+annotate (GROUP BY по ordering)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        base = self._base_qs()
        agg = base.aggregate(lo=Min('price'), hi=Max('price'))
        price_lo = int(agg['lo'] or 0)
        price_hi = int(agg['hi'] or 0)
        # як у дизайні: округлення діапазону
        if price_lo:
            price_lo = (price_lo // 10) * 10
        if price_hi:
            price_hi = ((price_hi + 9) // 10) * 10

        cur_min = self._decimal(self.request.GET.get('price_min'))
        cur_max = self._decimal(self.request.GET.get('price_max'))
        current_price_min = int(cur_min) if cur_min is not None else price_lo
        current_price_max = int(cur_max) if cur_max is not None else price_hi
        if current_price_min > current_price_max:
            current_price_min, current_price_max = current_price_max, current_price_min

        filter_groups = []
        filter_attrs = {attr.slug: attr for attr in self._filterable_attrs()}
        for index, attr in enumerate(self._filterable_attrs()):
            counted = (
                self._filter_counts(base, skip_key=attr.slug)
                .filter(attributes__attribute=attr)
                .order_by()
                .values('attributes__slug')
                .annotate(c=Count('id', distinct=True))
            )
            count_map = {row['attributes__slug']: row['c'] for row in counted}
            options = []
            for val in attr.values.all():
                selected = val.slug in self.request.GET.getlist(attr.slug)
                count = count_map.get(val.slug, 0)
                options.append(
                    {
                        'value': val,
                        'count': count,
                        'selected': selected,
                        'disabled': (not selected) and count == 0,
                    }
                )
            if not any(opt['count'] or opt['selected'] for opt in options):
                continue
            filter_groups.append(
                {
                    'attribute': attr,
                    'title': attr.display_name(),
                    'open': index < FILTER_OPEN_COUNT,
                    'options': options,
                }
            )

        selected_chips = []
        for attr in filter_attrs.values():
            for slug in self.request.GET.getlist(attr.slug):
                val = AttributeValue.objects.filter(attribute=attr, slug=slug).first()
                if val:
                    selected_chips.append(
                        {'label': val.display_value(), 'key': attr.slug, 'slug': slug}
                    )

        sku = self.request.GET.get('sku', '').strip()
        if sku:
            selected_chips.append(
                {'label': tr('Артикул: {sku}').format(sku=sku), 'key': 'sku', 'slug': sku}
            )

        if current_price_min > price_lo or current_price_max < price_hi:
            lo_l = f'{current_price_min:,}'.replace(',', ' ') + ' ₴'
            hi_l = f'{current_price_max:,}'.replace(',', ' ') + ' ₴'
            selected_chips.append(
                {'label': f'{lo_l} – {hi_l}', 'key': 'price', 'slug': ''}
            )

        sort = self.request.GET.get('sort', 'default')
        from pages.cms_content import get_block_text
        from pages.i18n_lib import site_lang_code

        lang = site_lang_code()
        sorts = [
            ('default', get_block_text('catalog', 'sort_popular', lang=lang)),
            ('cheap', get_block_text('catalog', 'sort_cheap', lang=lang)),
            ('expensive', get_block_text('catalog', 'sort_expensive', lang=lang)),
            ('rating', get_block_text('catalog', 'sort_rating', lang=lang)),
            ('new', get_block_text('catalog', 'sort_new', lang=lang)),
        ]
        total = ctx['page_obj'].paginator.count
        shown = min(ctx['page_obj'].end_index(), total) if total else 0
        limit = self.get_paginate_by(None)
        chrome = catalog_chrome(self.request)
        listing_title = chrome['title'] or tr('Циліндрові врізні замки')
        ctx.update(
            {
                'category': self.category,
                'title': (
                    self.category.card_name(get_language() or 'ua')
                    if self.category
                    else listing_title
                ),
                'catalog_empty': chrome['empty'],
                'catalog_filters_title': chrome['filters_title'],
                'count_label': tr('Знайдено {n} {word}').format(
                    n=total, word=plural_goods(total)
                ),
                'category_chips': category_nav_chips(self.category),
                'filter_groups': filter_groups,
                'selected_chips': selected_chips,
                'price_lo': price_lo,
                'price_hi': price_hi,
                'current_price_min': current_price_min,
                'current_price_max': current_price_max,
                'current_sku': sku,
                'current_sort': sort,
                'sorts': sorts,
                'sort_label': dict(sorts).get(sort, sorts[0][1]),
                'query_q': self.request.GET.get('q', ''),
                'shown_label': tr('Показано {shown} з {total}').format(
                    shown=shown, total=total
                ),
                'next_limit': limit + PAGE_SIZE,
                'has_more': shown < total,
                'page_size': PAGE_SIZE,
                'is_htmx': self.request.headers.get('HX-Request') == 'true',
            }
        )
        if self.request.headers.get('HX-Request') == 'true':
            swap = self.request.headers.get('HX-Target', '')
            if swap in ('product-grid', '#product-grid'):
                self.template_name = 'catalog/partials/product_cards.html'
            else:
                self.template_name = 'catalog/partials/product_grid.html'
        return ctx


class ProductDetailView(DetailView):
    model = Product
    template_name = 'catalog/product.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'

    ACCORDIONS = [
        {
            'id': 'd',
            'icon': 'truck',
            'title': 'Доставка',
            'hint': 'від 1 дня',
            'rows': [
                ('Нова Пошта, відділення', '1–2 дні · за тарифами'),
                ('Кур’єр по Києву', 'в день замовлення'),
                ('Самовивіз з магазину', 'безкоштовно'),
            ],
        },
        {
            'id': 'p',
            'icon': 'card',
            'title': 'Оплата',
            'hint': 'карткою або при отриманні',
            'rows': [
                ('Карткою онлайн', 'Visa, Mastercard'),
                ('Apple Pay / Google Pay', 'миттєво'),
                ('Накладений платіж', 'при отриманні'),
                ('Безготівковий розрахунок', 'для юросіб'),
            ],
        },
        {
            'id': 'w',
            'icon': 'shield',
            'title': 'Гарантія',
            'hint': '12 місяців',
            'rows': [
                ('Гарантія виробника', '12 місяців'),
                ('Обмін та повернення', '14 днів'),
                ('Сервісна заміна ключів', 'за кодовою карткою'),
            ],
        },
    ]

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related(
            'category', 'category__parent'
        ).prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.order_by('sort_order', 'id')),
            Prefetch(
                'attributes',
                queryset=AttributeValue.objects.select_related('attribute', 'attribute__group'),
            ),
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = self.object
        wishlist = WishlistService(self.request)
        variants, colors, sizes = build_variant_context(product)

        spec_rows = product_spec_rows(product)
        description_html = product_description_html(product, self.request)
        measure_title, measure_text = resolve_measure(product.category)
        reviews = published_reviews_for(product)

        accordions = []
        for block in self.ACCORDIONS:
            accordions.append(
                {
                    **block,
                    'title': tr(block['title']),
                    'hint': tr(block['hint']),
                    'rows': [(tr(a), tr(b)) for a, b in block['rows']],
                }
            )

        ctx.update(
            {
                'in_wishlist': wishlist.contains(product.pk),
                'spec_rows': spec_rows,
                'description_html': description_html,
                'accordions': accordions,
                'variant_colors': colors,
                'variant_sizes': sizes,
                'variants_json': json.dumps(variants, ensure_ascii=False),
                'current_color': product.color_code,
                'current_size': product.size_mm,
                'measure_title': measure_title,
                'measure_text': measure_text,
                'reviews': reviews,
                'reviews_visible': INITIAL_VISIBLE,
                'review_stats': review_summary(product, reviews),
                'product_brand': product_brand(product),
                'review_form': ReviewForm(),
                'review_sent': self.request.GET.get('review') == 'sent',
            }
        )
        return ctx
