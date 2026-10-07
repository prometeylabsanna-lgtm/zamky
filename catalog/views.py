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

    def get_queryset(self):
        return Product.objects.filter(is_active=True).prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.order_by('sort_order', 'id')),
            'attributes__attribute',
            'category',
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = self.object
        related = (
            Product.objects.filter(is_active=True, category=product.category)
            .exclude(pk=product.pk)
            .prefetch_related('images')[:8]
        )
        wishlist = WishlistService(self.request)
        attrs = {}
        for av in product.attributes.select_related('attribute'):
            attrs.setdefault(av.attribute.slug, []).append(av)
        ctx.update(
            {
                'related': related,
                'in_wishlist': wishlist.contains(product.pk),
                'attr_map': attrs,
            }
        )
        return ctx
