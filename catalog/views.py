import json
from decimal import Decimal, InvalidOperation

from django.db.models import Count, Max, Min, Prefetch, Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, ListView, TemplateView

from cart.services import WishlistService
from orders.models import DeliveryDistrict
from pages.i18n_lib import plural_goods, tr

from .models import Attribute, AttributeValue, Category, Product, ProductImage

SORT_MAP = {
    'default': ('catalog_order', 'name'),
    'cheap': ('price', 'catalog_order'),
    'expensive': ('-price', 'catalog_order'),
    'new': ('-is_new', 'catalog_order'),
    'rating': ('-rating', 'catalog_order'),
}

FILTER_TITLES = {
    'brand': 'Виробник/Бренд',
    'country': 'Країна виробництва',
    'color': 'Колір/покриття',
    'mech': 'Тип механізму',
}

FILTER_OPEN_DEFAULT = {
    'brand': True,
    'country': True,
    'color': False,
    'mech': True,
}

PAGE_SIZE = 12


class HomeView(TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cats = Category.objects.filter(is_active=True, parent__isnull=True).order_by(
            'sort_order', 'name'
        )
        hits = (
            Product.objects.filter(is_active=True, is_hit=True)
            .prefetch_related('images')
            .order_by('catalog_order', 'pk')[:8]
        )
        news = (
            Product.objects.filter(is_active=True, is_new=True)
            .prefetch_related('images')
            .order_by('catalog_order', 'pk')[:8]
        )
        if not hits:
            hits = Product.objects.filter(is_active=True).prefetch_related('images').order_by(
                'catalog_order'
            )[:8]
        if not news:
            news = (
                Product.objects.filter(is_active=True)
                .order_by('-created_at')
                .prefetch_related('images')[:8]
            )

        district = None
        is_city = False
        slug = self.kwargs.get('district_slug')
        city_slug = self.kwargs.get('city_slug')
        if slug:
            district = DeliveryDistrict.objects.filter(slug=slug, is_active=True).first()
            if district:
                self.request.session['district_slug'] = district.slug
        elif city_slug == 'kyiv' or self.request.path.rstrip('/').endswith('/kyiv'):
            is_city = True

        features = [
            {
                'title': tr('Надійні\nзамки'),
                'text': tr('Перевірені рішення\nдля захисту вашого дом'),
                'icon': 'shield',
            },
            {
                'title': tr('Популярні\nбренди'),
                'text': 'Mottura, Cisa, Elbor, Guardian,\nApecs, Securemme, Kale',
                'icon': 'award',
            },
            {
                'title': tr('Допомога\nу виборі'),
                'text': tr('Підберемо замок або\nсерцевину під ваші двері'),
                'icon': 'chat',
            },
            {
                'title': tr('Доставка\nпо Україні'),
                'text': tr('Швидко відправляємо\nзамовлення'),
                'icon': 'pin',
            },
        ]
        if district:
            features = [
                f
                if i != 3
                else {
                    'title': tr('Доставка\nпо району'),
                    'text': tr('{note}\nпо {district} району').format(
                        note=tr(district.delivery_note),
                        district=tr(district.name_locative),
                    ),
                    'icon': 'pin',
                }
                for i, f in enumerate(features)
            ]

        ctx.update(
            {
                'categories': cats,
                'hits': hits,
                'news': news,
                'district': district,
                'is_city': is_city,
                'other_districts': DeliveryDistrict.objects.filter(is_active=True).exclude(
                    pk=getattr(district, 'pk', None)
                ),
                'features': features,
            }
        )
        return ctx


class CatalogView(ListView):
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
            qs = qs.filter(Q(category=self.category) | Q(category__parent=self.category))

        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(brand__icontains=q))

        sku = self.request.GET.get('sku', '').strip()
        if sku:
            qs = qs.filter(sku__icontains=sku)

        for key in ('brand', 'country', 'color', 'mech'):
            values = self.request.GET.getlist(key)
            if values:
                qs = qs.filter(attributes__slug__in=values, attributes__attribute__slug=key)

        price_min = self._decimal(self.request.GET.get('price_min'))
        price_max = self._decimal(self.request.GET.get('price_max'))
        if price_min is not None:
            qs = qs.filter(price__gte=price_min)
        if price_max is not None:
            qs = qs.filter(price__lte=price_max)

        sort = self.request.GET.get('sort', 'default')
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

    def _base_qs(self):
        base = self._catalog_products()
        if self.category:
            base = base.filter(Q(category=self.category) | Q(category__parent=self.category))
        return base

    def _filter_counts(self, base, skip_key=None):
        """Лічильники опцій з урахуванням інших активних фільтрів (як у дизайні)."""
        qs = base
        for key in ('brand', 'country', 'color', 'mech'):
            if key == skip_key:
                continue
            values = self.request.GET.getlist(key)
            if values:
                qs = qs.filter(attributes__slug__in=values, attributes__attribute__slug=key)
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
        filter_attrs = {
            a.slug: a
            for a in Attribute.objects.filter(filterable=True, slug__in=FILTER_TITLES).prefetch_related(
                'values'
            )
        }
        for slug in FILTER_TITLES:
            attr = filter_attrs.get(slug)
            if not attr:
                continue
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
            # порядок опцій як у Catalog.dc.html
            value_order = {
                'brand': ['ABARO', 'Mottura', 'Cisa', 'Kale', 'Apecs'],
                'country': ['Туреччина', 'Італія', 'Китай'],
                'color': ['Латунь', 'Нікель', 'Чорний'],
                'mech': ['Ключ / ключ', 'Ключ / тумблер', 'Половинчастий'],
            }.get(attr.slug)
            if value_order:
                options.sort(
                    key=lambda o: value_order.index(o['value'].value)
                    if o['value'].value in value_order
                    else 99
                )
            filter_groups.append(
                {
                    'attribute': attr,
                    'title': tr(FILTER_TITLES.get(attr.slug, attr.name)),
                    'open': FILTER_OPEN_DEFAULT.get(attr.slug, True),
                    'options': options,
                }
            )

        selected_chips = []
        for attr in filter_attrs.values():
            for slug in self.request.GET.getlist(attr.slug):
                val = AttributeValue.objects.filter(attribute=attr, slug=slug).first()
                if val:
                    selected_chips.append(
                        {'label': tr(val.value), 'key': attr.slug, 'slug': slug}
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
        sorts = [
            ('default', tr('За замовчуванням')),
            ('cheap', tr('Спочатку дешевші')),
            ('expensive', tr('Спочатку дорожчі')),
            ('rating', tr('За рейтингом')),
            ('new', tr('Спочатку новинки')),
        ]
        total = ctx['page_obj'].paginator.count
        shown = min(ctx['page_obj'].end_index(), total) if total else 0
        limit = self.get_paginate_by(None)
        ctx.update(
            {
                'category': self.category,
                'title': tr(self.category.name)
                if self.category
                else tr('Циліндрові врізні замки'),
                'count_label': f'{total} {plural_goods(total)}',
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
        return Product.objects.filter(is_active=True).select_related('family', 'category').prefetch_related(
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
        variants = []
        colors = []
        sizes = []

        def _variant_payload(v):
            imgs = [
                {'src': img.image.url, 'alt': img.alt or v.name}
                for img in v.images.all()
            ]
            return {
                'id': v.pk,
                'sku': v.sku,
                'slug': v.slug,
                'url': v.get_absolute_url(),
                'name': tr(v.name),
                'price': int(v.price),
                'old_price': int(v.old_price) if v.old_price else None,
                'discount': v.discount_percent,
                'stock': int(v.stock or 0),
                'status': v.stock_status,
                'badge': v.stock_label,
                'stock_note': v.stock_note,
                'color': v.color_code or '',
                'color_label': tr(v.color_label),
                'size': v.size_mm or 0,
                'size_a': v.size_a,
                'size_b': v.size_b,
                'size_label': v.size_label,
                'cover': tr(v.cover),
                'images': imgs,
                'add_url': reverse('cart:add', kwargs={'pk': v.pk}),
                'quick_url': reverse('orders:quick', kwargs={'pk': v.pk}),
                'wishlist_url': reverse('cart:wishlist', kwargs={'pk': v.pk}),
            }

        if product.family_id:
            family_qs = (
                Product.objects.filter(is_active=True, family=product.family)
                .prefetch_related(
                    Prefetch('images', queryset=ProductImage.objects.order_by('sort_order', 'id'))
                )
                .order_by('size_mm', 'color_code')
            )
            seen_colors = {}
            seen_sizes = {}
            for v in family_qs:
                variants.append(_variant_payload(v))
                if v.color_code and v.color_code not in seen_colors:
                    primary = v.images.first()
                    seen_colors[v.color_code] = {
                        'code': v.color_code,
                        'label': tr(v.color_label),
                        'img': primary.image.url if primary else '',
                    }
                if v.size_mm and v.size_mm not in seen_sizes:
                    seen_sizes[v.size_mm] = {
                        'len': v.size_mm,
                        'a': v.size_a,
                        'b': v.size_b,
                        'label': v.size_label,
                    }
            color_order = {'G': 0, 'N': 1, 'B': 2}
            colors = sorted(
                seen_colors.values(),
                key=lambda x: color_order.get(x['code'], 99),
            )
            sizes = sorted(seen_sizes.values(), key=lambda x: x['len'])
        else:
            # Товар без family — все одно потрібен варіант для qty/stock у JS.
            variants.append(_variant_payload(product))

        spec_groups = self._spec_groups(product)
        description_parts = []
        desc = product.description or (product.family.description if product.family_id else '')
        if desc:
            description_parts = [tr(p.strip()) for p in desc.split('\n\n') if p.strip()]

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
                'spec_groups': spec_groups,
                'description_parts': description_parts,
                'accordions': accordions,
                'variant_colors': colors,
                'variant_sizes': sizes,
                'variants_json': json.dumps(variants, ensure_ascii=False),
                'current_color': product.color_code,
                'current_size': product.size_mm,
            }
        )
        return ctx

    def _spec_groups(self, product):
        rows_by_group = {}
        for av in product.attributes.all():
            attr = av.attribute
            if attr.group_id and attr.group.slug == 'filters':
                continue
            group = attr.group
            key = group.pk if group else 0
            title = tr(group.name) if group else tr('Інше')
            order = group.sort_order if group else 999
            bucket = rows_by_group.setdefault(key, {'title': title, 'order': order, 'rows': []})
            bucket['rows'].append(
                {'k': tr(attr.name), 'v': tr(av.value), 'order': attr.sort_order}
            )
        groups = sorted(rows_by_group.values(), key=lambda g: g['order'])
        for g in groups:
            g['rows'] = sorted(g['rows'], key=lambda r: r['order'])
            for i, row in enumerate(g['rows']):
                row['zebra'] = i % 2 == 1
        return groups
