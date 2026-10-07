from decimal import Decimal

from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField('Назва', max_length=200)
    slug = models.SlugField('Slug', max_length=220, unique=True)
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
            base = slugify(self.name) or 'category'
            slug = base
            i = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{i}'
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalog:category', kwargs={'slug': self.slug})


class Attribute(models.Model):
    name = models.CharField('Назва', max_length=120)
    slug = models.SlugField('Slug', max_length=140, unique=True)
    filterable = models.BooleanField('У фільтрах', default=True)
    sort_order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Атрибут'
        verbose_name_plural = 'Атрибути'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class AttributeValue(models.Model):
    attribute = models.ForeignKey(
        Attribute,
        related_name='values',
        on_delete=models.CASCADE,
        verbose_name='Атрибут',
    )
    value = models.CharField('Значення', max_length=200)
    slug = models.SlugField('Slug', max_length=220)
    sort_order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Значення атрибута'
        verbose_name_plural = 'Значення атрибутів'
        ordering = ['sort_order', 'value']
        unique_together = [('attribute', 'slug')]

    def __str__(self):
        return f'{self.attribute.name}: {self.value}'


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.PROTECT,
        verbose_name='Категорія',
    )
    name = models.CharField('Назва', max_length=300)
    slug = models.SlugField('Slug', max_length=320, unique=True)
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
    brand = models.CharField('Бренд', max_length=100, blank=True)
    short_description = models.TextField('Короткий опис', blank=True)
    description = models.TextField('Опис', blank=True)
    attributes = models.ManyToManyField(
        AttributeValue,
        through='ProductAttribute',
        related_name='products',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товари'
        ordering = ['-is_hit', '-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or slugify(self.sku) or 'product'
            slug = base
            i = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{i}'
                i += 1
            self.slug = slug
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
        return {
            'in': 'В наявності',
            'low': 'Закінчується',
            'out': 'Немає в наявності',
        }[self.stock_status]

    @property
    def primary_image(self):
        img = self.images.order_by('sort_order', 'id').first()
        return img

    @property
    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return int(((self.old_price - self.price) / self.old_price) * 100)
        return 0

    def format_price(self, value=None):
        v = value if value is not None else self.price
        n = int(Decimal(v))
        return f'{n:,}'.replace(',', ' ') + ' ₴'


class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_attributes')
    attribute_value = models.ForeignKey(AttributeValue, on_delete=models.CASCADE)

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
