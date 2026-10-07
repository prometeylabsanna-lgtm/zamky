import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone


class DeliveryDistrict(models.Model):
    slug = models.SlugField('Slug', max_length=120, unique=True)
    name = models.CharField('Назва', max_length=200)
    short = models.CharField('Коротка', max_length=100)
    name_locative = models.CharField('Місцевий відмінок', max_length=200, blank=True)
    delivery_note = models.CharField('Доставка', max_length=200, blank=True)
    areas = models.JSONField('Мікрорайони', default=list, blank=True)
    h1 = models.CharField('H1', max_length=300, blank=True)
    seo_text = models.TextField('SEO текст', blank=True)
    is_active = models.BooleanField('Активний', default=True)
    sort_order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Район доставки'
        verbose_name_plural = 'Райони доставки'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'Нове'
        CONFIRMED = 'confirmed', 'Підтверджено'
        SHIPPED = 'shipped', 'Відправлено'
        DONE = 'done', 'Виконано'
        CANCELLED = 'cancelled', 'Скасовано'

    class DeliveryMethod(models.TextChoices):
        NP = 'np', 'Нова Пошта'
        COURIER = 'courier', 'Курʼєр по Києву'
        PICKUP = 'pickup', 'Самовивіз'

    class PaymentMethod(models.TextChoices):
        COD = 'cod', 'Накладений платіж'
        CARD = 'card', 'Оплата карткою'
        INVOICE = 'invoice', 'Рахунок для юросіб'

    number = models.CharField('Номер', max_length=32, unique=True, editable=False)
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    first_name = models.CharField('Імʼя', max_length=100)
    last_name = models.CharField('Прізвище', max_length=100, blank=True)
    phone = models.CharField('Телефон', max_length=32)
    email = models.EmailField('Email', blank=True)
    district = models.ForeignKey(
        DeliveryDistrict,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Район',
        related_name='orders',
    )
    delivery_method = models.CharField(
        'Доставка',
        max_length=20,
        choices=DeliveryMethod.choices,
        default=DeliveryMethod.NP,
    )
    payment_method = models.CharField(
        'Оплата',
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.COD,
    )
    address = models.CharField('Адреса / відділення', max_length=300, blank=True)
    comment = models.TextField('Коментар', blank=True)
    subtotal = models.DecimalField('Сума товарів', max_digits=12, decimal_places=2, default=Decimal('0'))
    delivery_price = models.DecimalField('Доставка', max_digits=10, decimal_places=2, default=Decimal('0'))
    total = models.DecimalField('Разом', max_digits=12, decimal_places=2, default=Decimal('0'))
    idempotency_key = models.CharField(
        'Idempotency key',
        max_length=64,
        unique=True,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'
        ordering = ['-created_at']

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        if not self.number:
            stamp = timezone.now().strftime('%y%m%d')
            self.number = f'ZM-{stamp}-{uuid.uuid4().hex[:6].upper()}'
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE,
        verbose_name='Замовлення',
    )
    product = models.ForeignKey(
        'catalog.Product',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Товар',
    )
    product_name = models.CharField('Назва', max_length=300)
    sku = models.CharField('Артикул', max_length=64)
    unit_price = models.DecimalField('Ціна', max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField('Кількість', default=1)
    line_total = models.DecimalField('Сума', max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Позиція замовлення'
        verbose_name_plural = 'Позиції замовлення'

    def __str__(self):
        return f'{self.sku} × {self.quantity}'
