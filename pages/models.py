from django.db import models


class ContactRequest(models.Model):
    class Topic(models.TextChoices):
        LOCK = 'lock', 'Підбір замка або циліндра'
        ORDER = 'order', 'Питання щодо замовлення'
        DELIVERY = 'delivery', 'Доставка і оплата'
        RETURN = 'return', 'Обмін та повернення'
        INSTALL = 'install', 'Монтаж'
        OTHER = 'other', 'Інше'

    name = models.CharField('Імʼя', max_length=120)
    phone = models.CharField('Телефон', max_length=32)
    email = models.EmailField('Email', blank=True)
    topic = models.CharField(
        'Тема',
        max_length=20,
        choices=Topic.choices,
        default=Topic.LOCK,
    )
    message = models.TextField('Повідомлення')
    consent = models.BooleanField('Згода', default=False)
    processed = models.BooleanField('Опрацьовано', default=False)
    idempotency_key = models.CharField(
        'Idempotency key',
        max_length=64,
        unique=True,
        db_index=True,
    )
    created_at = models.DateTimeField('Створено', auto_now_add=True)

    class Meta:
        verbose_name = 'Запит з форми'
        verbose_name_plural = 'Запити з форми'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} · {self.phone}'


from pages.models_extra import (  # noqa: E402
    BlogPost,
    CallbackRequest,
    InstallRequest,
    PhotoPickImage,
    PhotoPickRequest,
)

__all__ = [
    'ContactRequest',
    'CallbackRequest',
    'PhotoPickRequest',
    'PhotoPickImage',
    'InstallRequest',
    'BlogPost',
]
