from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.urls import reverse
from pages.slug_utils import ensure_unique_slug, should_rebuild_slug, slug_has_non_ascii

from .filter_sort import apply_auto_sort_order


class CategoryManager(models.Manager):
    def get_queryset(self):
        from catalog.db_compat import missing_category_columns

        qs = super().get_queryset()
        missing = missing_category_columns()
        if missing:
            qs = qs.defer(*missing)
        return qs


class Category(models.Model):
    name = models.CharField('Назва', max_length=200)
    name_ru = models.CharField('Назва (RU)', max_length=200, blank=True, default='')
    slug = models.SlugField('Слаг', max_length=220, unique=True)
    parent = models.ForeignKey(
        'self',
        verbose_name='Батьківська',
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.CASCADE,
    )
    logo = models.ImageField('Логотип', upload_to='categories/', blank=True)
    icon = models.CharField(
        'Іконка',
        max_length=32,
        blank=True,
        help_text='cyl | pad | shield | brand',
    )
    home_subtitle = models.CharField(
        'Підпис на головній',
        max_length=180,
        blank=True,
        default='',
    )
    home_subtitle_ru = models.CharField(
        'Підпис на головній (RU)',
        max_length=180,
        blank=True,
        default='',
    )
    measure_title = models.CharField(
        'Кнопка підказки',
        max_length=160,
        blank=True,
        default='',
        help_text='На картці товару біля розміру. Порожнє — з батьківської категорії.',
    )
    measure_title_ru = models.CharField(
        'Кнопка підказки (RU)',
        max_length=160,
        blank=True,
        default='',
    )
    measure_text = models.TextField(
        'Текст підказки',
        blank=True,
        default='',
        help_text='Пояснення після натискання кнопки. Порожнє — з батьківської категорії.',
    )
    measure_text_ru = models.TextField(
        'Текст підказки (RU)',
        blank=True,
        default='',
    )
    sort_order = models.PositiveIntegerField('Порядок', default=0)
    objects = CategoryManager()
    is_active = models.BooleanField('Активна', default=True)
    show_in_menu = models.BooleanField('Показувати в меню', default=True)
    show_on_home = models.BooleanField('Показувати на головній', default=True)

    class Meta:
        verbose_name = 'Категорія'
        verbose_name_plural = 'Категорії'
        ordering = ['sort_order', 'name']

    def __str__(self):
        from catalog.category_tree import category_path_label

        if self.parent_id:
            return category_path_label(self)
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug or slug_has_non_ascii(self.slug):
            self.slug = ensure_unique_slug(
                Category, self.name, instance_pk=self.pk, fallback='category'
            )
        apply_auto_sort_order(
            self, Category.objects.filter(parent_id=self.parent_id)
        )
        from catalog.db_compat import missing_category_columns

        missing = missing_category_columns()
        toggled = []
        if missing:
            update_fields = kwargs.get('update_fields')
            if update_fields is not None:
                kept = [name for name in update_fields if name not in missing]
                if not kept:
                    return
                kwargs['update_fields'] = kept
            elif self.pk:
                kwargs['update_fields'] = [
                    field.attname
                    for field in self._meta.local_concrete_fields
                    if not field.primary_key and field.name not in missing
                ]
            else:
                for name in missing:
                    field = self._meta.get_field(name)
                    toggled.append((field, field.generated))
                    field.generated = True
        try:
            super().save(*args, **kwargs)
        finally:
            for field, previous in toggled:
                field.generated = previous

    def get_absolute_url(self):
        return reverse('catalog:category', kwargs={'slug': self.slug})

    def card_name(self, lang: str | None = None) -> str:
        if lang is None:
            from django.utils.translation import get_language

            lang = get_language() or 'ua'
        if str(lang).lower().startswith('ru') and (self.name_ru or '').strip():
            return self.name_ru.strip()
        return self.name

    def card_subtitle(self, lang: str = 'ua') -> str:
        if str(lang).lower().startswith('ru') and (self.home_subtitle_ru or '').strip():
            return self.home_subtitle_ru.strip()
        return (self.home_subtitle or '').strip()


class AttributeGroup(models.Model):
    name = models.CharField('Назва', max_length=120)
    name_ru = models.CharField('Назва (RU)', max_length=120, blank=True, default='')
    slug = models.SlugField('Слаг', max_length=140, unique=True)
    sort_order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Група фільтрів'
        verbose_name_plural = 'Фільтри'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def display_name(self):
        from catalog.filter_i18n import localized_text

        return localized_text(self.name, self.name_ru)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = ensure_unique_slug(
                AttributeGroup, self.name, instance_pk=self.pk, fallback='group'
            )
        apply_auto_sort_order(self, AttributeGroup.objects.all())
        super().save(*args, **kwargs)


class Attribute(models.Model):
    name = models.CharField('Назва', max_length=120)
    name_ru = models.CharField('Назва (RU)', max_length=120, blank=True, default='')
    slug = models.SlugField('Слаг', max_length=140, unique=True)
    group = models.ForeignKey(
        AttributeGroup,
        verbose_name='Група',
        null=True,
        blank=True,
        related_name='attributes',
        on_delete=models.SET_NULL,
    )
    filterable = models.BooleanField('У фільтрах', default=True)
    sort_order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Фільтр'
        verbose_name_plural = 'Фільтри'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def display_name(self):
        from catalog.filter_i18n import localized_text

        return localized_text(self.name, self.name_ru)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = ensure_unique_slug(
                Attribute, self.name, instance_pk=self.pk, fallback='attr'
            )
        apply_auto_sort_order(self, Attribute.objects.all())
        super().save(*args, **kwargs)


class AttributeValue(models.Model):
    attribute = models.ForeignKey(
        Attribute,
        related_name='values',
        on_delete=models.CASCADE,
        verbose_name='Атрибут',
    )
    value = models.CharField('Значення', max_length=200)
    value_ru = models.CharField('Значення (RU)', max_length=200, blank=True, default='')
    slug = models.SlugField('Слаг', max_length=220)
    sort_order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Значення фільтра'
        verbose_name_plural = 'Значення фільтрів'
        ordering = ['sort_order', 'value']
        unique_together = [('attribute', 'slug')]

    def __str__(self):
        return f'{self.attribute.name}: {self.value}'

    def display_value(self):
        from catalog.filter_i18n import localized_text

        return localized_text(self.value, self.value_ru)

    def save(self, *args, **kwargs):
        extra = {'attribute_id': self.attribute_id} if self.attribute_id else None
        if should_rebuild_slug(self.value, self.slug, 'value'):
            self.slug = ensure_unique_slug(
                AttributeValue,
                self.value,
                instance_pk=self.pk,
                extra_filter=extra,
                fallback='value',
            )
        apply_auto_sort_order(
            self, AttributeValue.objects.filter(attribute_id=self.attribute_id)
        )
        super().save(*args, **kwargs)


COLOR_CHOICES = (
    ('G', 'Латунь'),
    ('N', 'Нікель'),
    ('B', 'Чорний'),
)
COLOR_LABELS = dict(COLOR_CHOICES)


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.PROTECT,
        verbose_name='Категорія',
        help_text='Категорію з товарами видалити не можна — спочатку перенесіть товари.',
    )
    name = models.CharField('Назва', max_length=300)
    slug = models.SlugField('Слаг', max_length=320, unique=True)
    sku = models.CharField('Артикул', max_length=64, unique=True)
    price = models.DecimalField('Ціна', max_digits=10, decimal_places=2)
    old_price = models.DecimalField(
        'Стара ціна',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    stock = models.PositiveIntegerField('Залишок', default=0)
    is_active = models.BooleanField('Активний', default=True)
    is_hit = models.BooleanField('Хіт продажу', default=False)
    is_new = models.BooleanField('Новинка', default=False)
    catalog_order = models.PositiveIntegerField('Порядок у каталозі', default=0, db_index=True)
    rating = models.PositiveSmallIntegerField('Рейтинг', default=4)
    reviews_count = models.PositiveIntegerField(
        'Кількість відгуків',
        default=0,
        help_text='Рахується автоматично з активних відгуків.',
    )
    reviews_avg = models.DecimalField(
        'Середня оцінка відгуків',
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        editable=False,
    )
    warranty_months = models.PositiveSmallIntegerField('Гарантія, місяців', default=12)
    brand = models.CharField('Бренд', max_length=100, blank=True)
    color_code = models.CharField(
        'Колір серцевини',
        max_length=8,
        blank=True,
        choices=COLOR_CHOICES,
        help_text='Кружечки на сторінці товару та в кошику.',
    )
    color_label = models.CharField('Колір', max_length=64, blank=True)
    finish = models.CharField('Оздоблення', max_length=120, blank=True)
    cover = models.CharField('Покриття', max_length=120, blank=True)
    size_mm = models.PositiveIntegerField('Довжина, мм', null=True, blank=True)
    size_a = models.PositiveIntegerField('Розмір A', null=True, blank=True)
    size_b = models.PositiveIntegerField('Розмір B', null=True, blank=True)
    short_description = models.TextField('Короткий опис', blank=True)
    short_description_ru = models.TextField('Короткий опис (RU)', blank=True, default='')
    description = models.TextField('Опис', blank=True)
    description_ru = models.TextField('Опис (RU)', blank=True, default='')
    name_ru = models.CharField('Назва (RU)', max_length=300, blank=True, default='')
    seo_title = models.CharField('SEO заголовок', max_length=200, blank=True, default='')
    seo_title_ru = models.CharField('SEO заголовок (RU)', max_length=200, blank=True, default='')
    seo_description = models.CharField(
        'SEO опис', max_length=320, blank=True, default=''
    )
    seo_description_ru = models.CharField(
        'SEO опис (RU)', max_length=320, blank=True, default=''
    )
    canonical_url = models.CharField('Канонічний URL', max_length=512, blank=True, default='')
    og_image = models.ImageField('OG зображення', upload_to='products/og/', blank=True, null=True)
    attributes = models.ManyToManyField(
        AttributeValue,
        through='ProductAttribute',
        related_name='products',
        blank=True,
    )
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    updated_at = models.DateTimeField('Оновлено', auto_now=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товари'
        ordering = ['catalog_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug or slug_has_non_ascii(self.slug):
            self.slug = ensure_unique_slug(
                Product,
                self.name or self.sku or 'product',
                instance_pk=self.pk,
                fallback='product',
            )
        code = (self.color_code or '').strip()
        if code and not (self.color_label or '').strip():
            mapped = COLOR_LABELS.get(code)
            if mapped:
                self.color_label = mapped
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalog:product', kwargs={'slug': self.slug})

    def card_name(self, lang: str | None = None) -> str:
        if lang is None:
            from django.utils.translation import get_language

            lang = get_language() or 'ua'
        if str(lang).lower().startswith('ru') and (self.name_ru or '').strip():
            return self.name_ru.strip()
        return self.name

    @property
    def stock_status(self):
        if self.stock <= 0:
            return 'out'
        if self.stock <= 3:
            return 'low'
        return 'in'

    def _shop_text(self, key: str) -> str:
        from pages.cms_content import get_block_text
        from pages.i18n_lib import site_lang_code

        return get_block_text('product', key, lang=site_lang_code())

    @property
    def stock_label(self):
        return self._shop_text({
            'in': 'stock_in',
            'low': 'stock_low',
            'out': 'stock_out',
        }[self.stock_status])

    @property
    def stock_note(self):
        if self.stock_status == 'out':
            return self._shop_text('stock_note_out')
        if self.stock_status == 'low':
            return self._shop_text('stock_note_low').replace('{n}', str(self.stock))
        return self._shop_text('stock_note_in')

    @property
    def primary_image(self):
        img = self.images.order_by('sort_order', 'id').first()
        return img

    @property
    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            ratio = (Decimal('1') - (self.price / self.old_price)) * Decimal('100')
            return int(ratio.quantize(Decimal('1')))
        return 0

    @property
    def reviews_label(self):
        from catalog.product_meta import reviews_label as _reviews_label

        return _reviews_label(self.reviews_count)

    @property
    def display_rating(self):
        if (self.reviews_count or 0) > 0 and self.reviews_avg is not None:
            return float(self.reviews_avg)
        return float(self.rating or 0)

    @property
    def display_stars(self):
        return int(self.display_rating + 0.5)

    @property
    def display_score(self):
        return f'{self.display_rating:.1f}'

    @property
    def warranty_label(self):
        from catalog.product_meta import warranty_label as _warranty_label

        return _warranty_label(self.warranty_months)

    @property
    def size_label(self):
        if self.size_a and self.size_b:
            return f'{self.size_a}×{self.size_b}'
        return ''

    def format_price(self, value=None):
        v = Decimal(value if value is not None else self.price).quantize(Decimal('0.01'))
        if v == v.to_integral_value():
            n = int(v)
            return f'{n:,}'.replace(',', ' ') + ' ₴'
        whole, frac = f'{v:.2f}'.split('.')
        whole = f'{int(whole):,}'.replace(',', ' ')
        return f'{whole},{frac} ₴'

    @property
    def price_display(self):
        return self.format_price()

    @property
    def old_price_display(self):
        if self.old_price:
            return self.format_price(self.old_price)
        return ''


class ProductAttribute(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='product_attributes',
        verbose_name='Товар',
    )
    attribute_value = models.ForeignKey(
        AttributeValue,
        on_delete=models.CASCADE,
        verbose_name='Значення атрибута',
    )

    class Meta:
        verbose_name = 'Фільтр товару'
        verbose_name_plural = 'Фільтри товару'
        unique_together = [('product', 'attribute_value')]

    def __str__(self):
        return f'{self.product.sku}: {self.attribute_value}'


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        related_name='images',
        on_delete=models.CASCADE,
        verbose_name='Товар',
    )
    image = models.ImageField('Зображення', upload_to='products/')
    alt = models.CharField('Alt', max_length=200, blank=True)
    sort_order = models.PositiveIntegerField('Порядок', default=0)
    is_primary = models.BooleanField('Головне', default=False)

    class Meta:
        verbose_name = 'Зображення товару'
        verbose_name_plural = 'Зображення товарів'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'{self.product.sku} #{self.pk}'

    def save(self, *args, **kwargs):
        apply_auto_sort_order(
            self, ProductImage.objects.filter(product_id=self.product_id)
        )
        super().save(*args, **kwargs)


class Review(models.Model):
    """Відгук покупця про товар. З сайту приходить неопублікованим — на модерацію."""

    RATING_CHOICES = [(i, '★' * i) for i in range(5, 0, -1)]

    product = models.ForeignKey(
        Product,
        related_name='reviews',
        on_delete=models.CASCADE,
        verbose_name='Товар',
    )
    author_name = models.CharField('Імʼя', max_length=120)
    rating = models.PositiveSmallIntegerField('Оцінка', choices=RATING_CHOICES, default=5)
    text = models.TextField('Текст відгуку')
    created_at = models.DateTimeField(
        'Дата', default=timezone.now, help_text='Показується на сайті у форматі дд.мм.рррр.'
    )
    is_published = models.BooleanField(
        'Активний',
        default=True,
        help_text='Без галочки відгук не видно на сайті.',
    )
    phone = models.CharField('Телефон', max_length=32, blank=True, help_text='Не публікується.')
    email = models.EmailField('Email', blank=True, help_text='Не публікується.')

    class Meta:
        verbose_name = 'Відгук'
        verbose_name_plural = 'Відгуки'
        ordering = ['-created_at', '-id']
        indexes = [models.Index(fields=['product', 'is_published', '-created_at'])]

    def __str__(self):
        return f'{self.author_name} · {self.rating}★'
