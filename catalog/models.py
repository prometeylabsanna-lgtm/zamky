from decimal import Decimal

from django.db import models
from django.urls import reverse
from pages.slug_utils import ensure_unique_slug


class Category(models.Model):
    name = models.CharField('Назва', max_length=200)
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
    sort_order = models.PositiveIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активна', default=True)

    class Meta:
        verbose_name = 'Категорія'
        verbose_name_plural = 'Категорії'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = ensure_unique_slug(
                Category, self.name, instance_pk=self.pk, fallback='category'
            )
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalog:category', kwargs={'slug': self.slug})


class AttributeGroup(models.Model):
    name = models.CharField('Назва', max_length=120)
    slug = models.SlugField('Слаг', max_length=140, unique=True)
    sort_order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Група характеристик'
        verbose_name_plural = 'Групи характеристик'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = ensure_unique_slug(
                AttributeGroup, self.name, instance_pk=self.pk, fallback='group'
            )
        super().save(*args, **kwargs)


class Attribute(models.Model):
    name = models.CharField('Назва', max_length=120)
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
        verbose_name = 'Атрибут'
        verbose_name_plural = 'Атрибути'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = ensure_unique_slug(
                Attribute, self.name, instance_pk=self.pk, fallback='attr'
            )
        super().save(*args, **kwargs)


class AttributeValue(models.Model):
    attribute = models.ForeignKey(
        Attribute,
        related_name='values',
        on_delete=models.CASCADE,
        verbose_name='Атрибут',
    )
    value = models.CharField('Значення', max_length=200)
    slug = models.SlugField('Слаг', max_length=220)
    sort_order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Значення атрибута'
        verbose_name_plural = 'Значення атрибутів'
        ordering = ['sort_order', 'value']
        unique_together = [('attribute', 'slug')]

    def __str__(self):
        return f'{self.attribute.name}: {self.value}'

    def save(self, *args, **kwargs):
        if not self.slug:
            extra = {'attribute_id': self.attribute_id} if self.attribute_id else None
            self.slug = ensure_unique_slug(
                AttributeValue,
                self.value,
                instance_pk=self.pk,
                extra_filter=extra,
                fallback='value',
            )
        super().save(*args, **kwargs)


class ProductFamily(models.Model):
    name = models.CharField('Назва', max_length=200)
    slug = models.SlugField('Слаг', max_length=220, unique=True)
    brand = models.CharField('Бренд', max_length=100, blank=True)
    description = models.TextField('Опис', blank=True)
    short_description = models.TextField('Короткий опис', blank=True)

    class Meta:
        verbose_name = 'Сімʼя товарів'
        verbose_name_plural = 'Сімʼї товарів'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = ensure_unique_slug(
                ProductFamily, self.name, instance_pk=self.pk, fallback='family'
            )
        super().save(*args, **kwargs)


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.PROTECT,
        verbose_name='Категорія',
    )
    family = models.ForeignKey(
        ProductFamily,
        verbose_name='Сімʼя',
        null=True,
        blank=True,
        related_name='variants',
        on_delete=models.SET_NULL,
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
    brand = models.CharField('Бренд', max_length=100, blank=True)
    color_code = models.CharField('Код кольору', max_length=8, blank=True)
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
        if not self.slug:
            self.slug = ensure_unique_slug(
                Product,
                self.name or self.sku or 'product',
                instance_pk=self.pk,
                fallback='product',
            )
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalog:product', kwargs={'slug': self.slug})

    @property
    def stock_status(self):
        if self.stock <= 0:
            return 'out'
        if self.stock <= 3:
            return 'low'
        return 'in'

    @property
    def stock_label(self):
        from pages.i18n_lib import tr

        return {
            'in': tr('В наявності'),
            'low': tr('Закінчується'),
            'out': tr('Немає в наявності'),
        }[self.stock_status]

    @property
    def stock_note(self):
        from pages.i18n_lib import tr

        if self.stock_status == 'out':
            return tr('Повідомимо про надходження')
        if self.stock_status == 'low':
            return tr('Залишилось {n} шт.').format(n=self.stock)
        return tr('Відправимо сьогодні')

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
        verbose_name = 'Характеристика товару'
        verbose_name_plural = 'Характеристики товарів'
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
