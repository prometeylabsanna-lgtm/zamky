from django.db import models
from django.utils.text import slugify


class CallbackRequest(models.Model):
    name = models.CharField('Імʼя', max_length=120, blank=True)
    phone = models.CharField('Телефон', max_length=32)
    processed = models.BooleanField('Опрацьовано', default=False)
    idempotency_key = models.CharField(
        'Idempotency key',
        max_length=64,
        unique=True,
        db_index=True,
    )
    created_at = models.DateTimeField('Створено', auto_now_add=True)

    class Meta:
        verbose_name = 'Заявка на дзвінок'
        verbose_name_plural = 'Заявки на дзвінок'
        ordering = ['-created_at']

    def __str__(self):
        label = self.name or self.phone
        return f'{label} · {self.phone}'


class PhotoPickRequest(models.Model):
    class Channel(models.TextChoices):
        CALL = 'call', 'Дзвінок'
        VIBER = 'viber', 'Viber'
        TELEGRAM = 'telegram', 'Telegram'

    phone = models.CharField('Телефон', max_length=32)
    channel = models.CharField(
        'Канал звʼязку',
        max_length=16,
        choices=Channel.choices,
        default=Channel.CALL,
    )
    note = models.TextField('Примітка', blank=True)
    processed = models.BooleanField('Опрацьовано', default=False)
    idempotency_key = models.CharField(
        'Idempotency key',
        max_length=64,
        unique=True,
        db_index=True,
    )
    created_at = models.DateTimeField('Створено', auto_now_add=True)

    class Meta:
        verbose_name = 'Запит підбору по фото'
        verbose_name_plural = 'Запити підбору по фото'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.phone} · {self.get_channel_display()}'


class PhotoPickImage(models.Model):
    request = models.ForeignKey(
        PhotoPickRequest,
        related_name='images',
        on_delete=models.CASCADE,
        verbose_name='Запит',
    )
    image = models.ImageField('Зображення', upload_to='picker/')
    created_at = models.DateTimeField('Створено', auto_now_add=True)

    class Meta:
        verbose_name = 'Фото до підбору'
        verbose_name_plural = 'Фото до підбору'
        ordering = ['created_at', 'id']

    def __str__(self):
        return f'Фото #{self.pk}'


class InstallRequest(models.Model):
    name = models.CharField('Імʼя', max_length=120)
    phone = models.CharField('Телефон', max_length=32)
    address = models.CharField('Адреса', max_length=255, blank=True)
    comment = models.TextField('Коментар', blank=True)
    processed = models.BooleanField('Опрацьовано', default=False)
    idempotency_key = models.CharField(
        'Idempotency key',
        max_length=64,
        unique=True,
        db_index=True,
    )
    created_at = models.DateTimeField('Створено', auto_now_add=True)

    class Meta:
        verbose_name = 'Заявка на установку'
        verbose_name_plural = 'Заявки на установку'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} · {self.phone}'


class BlogPost(models.Model):
    title = models.CharField('Заголовок', max_length=300)
    slug = models.SlugField('Slug', max_length=320, unique=True)
    excerpt = models.TextField('Короткий опис')
    body = models.TextField('Текст')
    cover = models.ImageField('Обкладинка', upload_to='blog/', blank=True)
    is_published = models.BooleanField('Опубліковано', default=True)
    sort_order = models.PositiveIntegerField('Порядок', default=0, db_index=True)
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    updated_at = models.DateTimeField('Оновлено', auto_now=True)

    class Meta:
        verbose_name = 'Стаття блогу'
        verbose_name_plural = 'Статті блогу'
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or 'post'
            slug = base
            i = 1
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{i}'
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)
