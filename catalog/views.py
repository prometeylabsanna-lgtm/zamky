import json
from decimal import Decimal, InvalidOperation

from django.db.models import Max, Min, Prefetch, Q
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView, TemplateView

from cart.services import WishlistService
from orders.models import DeliveryDistrict

from .models import Attribute, AttributeValue, Category, Product, ProductImage

SORT_MAP = {
    'default': ('-is_hit', '-created_at'),
    'cheap': ('price', 'name'),
    'expensive': ('-price', 'name'),
    'new': ('-is_new', '-created_at'),
    'rating': ('-is_hit', 'price'),
}


class HomeView(TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cats = Category.objects.filter(is_active=True, parent__isnull=True)
        hits = (
            Product.objects.filter(is_active=True, is_hit=True)
            .prefetch_related('images')[:12]
        )
        news = (
            Product.objects.filter(is_active=True, is_new=True)
            .prefetch_related('images')[:12]
        )
        if not hits:
            hits = Product.objects.filter(is_active=True).prefetch_related('images')[:8]
        if not news:
            news = Product.objects.filter(is_active=True).order_by('-created_at').prefetch_related('images')[:8]

        district = None
        slug = self.kwargs.get('district_slug') or self.request.session.get('district_slug')
        if slug:
            district = DeliveryDistrict.objects.filter(slug=slug, is_active=True).first()
            if district:
                self.request.session['district_slug'] = district.slug

        ctx.update(
            {
                'categories': cats,
                'hits': hits,
                'news': news,
                'district': district,
                'other_districts': DeliveryDistrict.objects.filter(is_active=True).exclude(
                    pk=getattr(district, 'pk', None)
                ),
                'features': [
                    {'title': 'Надійні\nзамки', 'text': 'Перевірені рішення\nдля захисту вашого дому', 'icon': 'shield'},
                    {'title': 'Популярні\nбренди', 'text': 'Mottura, Cisa, Elbor, Guardian,\nApecs, Securemme, Kale', 'icon': 'award'},
                    {'title': 'Допомога\nу виборі', 'text': 'Підберемо замок або\nсерцевину під ваші двері', 'icon': 'chat'},
                    {'title': 'Доставка\nпо Україні', 'text': 'Швидко відправляємо\nзамовлення', 'icon': 'pin'},
                ],
            }
        )
        return ctx


class CatalogView(ListView):
    model = Product
    template_name = 'catalog/catalog.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).prefetch_related('images', 'attributes')
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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        base = Product.objects.filter(is_active=True)
        if self.category:
            base = base.filter(Q(category=self.category) | Q(category__parent=self.category))
        agg = base.aggregate(lo=Min('price'), hi=Max('price'))
        price_lo = int(agg['lo'] or 0)
        price_hi = int(agg['hi'] or 0)

        filter_groups = []
        for attr in Attribute.objects.filter(filterable=True).prefetch_related('values'):
            options = []
            for val in attr.values.all():
                count = base.filter(attributes=val).count()
                selected = val.slug in self.request.GET.getlist(attr.slug)
                options.append({'value': val, 'count': count, 'selected': selected})
            filter_groups.append({'attribute': attr, 'options': options})

        selected_chips = []
        for attr in Attribute.objects.filter(filterable=True):
            for slug in self.request.GET.getlist(attr.slug):
                val = AttributeValue.objects.filter(attribute=attr, slug=slug).first()
                if val:
                    selected_chips.append({'label': val.value, 'key': attr.slug, 'slug': slug})

        sku = self.request.GET.get('sku', '').strip()
        if sku:
            selected_chips.append({'label': f'Артикул: {sku}', 'key': 'sku', 'slug': sku})

        sort = self.request.GET.get('sort', 'default')
        sorts = [
            ('default', 'За замовчуванням'),
            ('cheap', 'Спочатку дешевші'),
            ('expensive', 'Спочатку дорожчі'),
            ('rating', 'За рейтингом'),
            ('new', 'Спочатку новинки'),
        ]
        ctx.update(
            {
                'category': self.category,
                'title': self.category.name if self.category else 'Циліндрові врізні замки',
                'filter_groups': filter_groups,
                'selected_chips': selected_chips,
                'price_lo': price_lo,
                'price_hi': price_hi,
                'current_price_min': self.request.GET.get('price_min', price_lo),
                'current_price_max': self.request.GET.get('price_max', price_hi),
                'current_sku': sku,
                'current_sort': sort,
                'sorts': sorts,
                'query_q': self.request.GET.get('q', ''),
                'is_htmx': self.request.headers.get('HX-Request') == 'true',
            }
        )
        if self.request.headers.get('HX-Request') == 'true':
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
                imgs = [
                    {
                        'src': img.image.url,
                        'alt': img.alt or v.name,
                    }
                    for img in v.images.all()
                ]
                variants.append(
                    {
                        'id': v.pk,
                        'sku': v.sku,
                        'slug': v.slug,
                        'url': v.get_absolute_url(),
                        'name': v.name,
                        'price': int(v.price),
                        'old_price': int(v.old_price) if v.old_price else None,
                        'discount': v.discount_percent,
                        'stock': v.stock,
                        'status': v.stock_status,
                        'badge': v.stock_label,
                        'stock_note': v.stock_note,
                        'color': v.color_code,
                        'color_label': v.color_label,
                        'size': v.size_mm,
                        'size_a': v.size_a,
                        'size_b': v.size_b,
                        'size_label': v.size_label,
                        'cover': v.cover,
                        'images': imgs,
                        'add_url': f'/cart/add/{v.pk}/',
                        'quick_url': f'/orders/quick/{v.pk}/',
                        'wishlist_url': f'/cart/wishlist/{v.pk}/',
                    }
                )
                if v.color_code and v.color_code not in seen_colors:
                    primary = v.images.first()
                    seen_colors[v.color_code] = {
                        'code': v.color_code,
                        'label': v.color_label,
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

        spec_groups = self._spec_groups(product)
        description_parts = []
        desc = product.description or (product.family.description if product.family_id else '')
        if desc:
            description_parts = [p.strip() for p in desc.split('\n\n') if p.strip()]

        ctx.update(
            {
                'in_wishlist': wishlist.contains(product.pk),
                'spec_groups': spec_groups,
                'description_parts': description_parts,
                'accordions': self.ACCORDIONS,
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
            title = group.name if group else 'Інше'
            order = group.sort_order if group else 999
            bucket = rows_by_group.setdefault(key, {'title': title, 'order': order, 'rows': []})
            bucket['rows'].append({'k': attr.name, 'v': av.value, 'order': attr.sort_order})
        groups = sorted(rows_by_group.values(), key=lambda g: g['order'])
        for g in groups:
            g['rows'] = sorted(g['rows'], key=lambda r: r['order'])
            for i, row in enumerate(g['rows']):
                row['zebra'] = i % 2 == 1
        return groups
