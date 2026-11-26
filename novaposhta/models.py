from django.db import models


class NPSyncRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = 'running', 'Виконується'
        SUCCESS = 'success', 'Успішно'
        FAILED = 'failed', 'Помилка'

    started_at = models.DateTimeField('Початок', auto_now_add=True, db_index=True)
    finished_at = models.DateTimeField('Завершення', null=True, blank=True)
    status = models.CharField(
        'Статус',
        max_length=16,
        choices=Status.choices,
        default=Status.RUNNING,
        db_index=True,
    )
    pages = models.PositiveIntegerField('Сторінок', default=0)
    received = models.PositiveIntegerField('Отримано', default=0)
    created = models.PositiveIntegerField('Створено', default=0)
    updated = models.PositiveIntegerField('Оновлено', default=0)
    deactivated = models.PositiveIntegerField('Деактивовано', default=0)
    message = models.TextField(
        'Повідомлення',
        blank=True,
        default='',
        help_text='Без секретів і ключа API.',
    )

    class Meta:
        verbose_name = 'Синхронізація НП'
        verbose_name_plural = 'Синхронізації НП'
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.get_status_display()} {self.started_at:%Y-%m-%d %H:%M}'


class NPCity(models.Model):
    ref = models.CharField('Ref', max_length=36, unique=True)
    name = models.CharField('Назва', max_length=255, blank=True, default='')
    name_ru = models.CharField('Назва RU', max_length=255, blank=True, default='')
    area = models.CharField('Область', max_length=255, blank=True, default='')
    region = models.CharField('Район', max_length=255, blank=True, default='')
    settlement_type = models.CharField('Тип населеного пункту', max_length=64, blank=True, default='')
    is_active = models.BooleanField('Активне', default=True)
    search_norm = models.TextField('Нормалізований пошук', blank=True, default='')
    updated_at = models.DateTimeField('Оновлено', auto_now=True)

    class Meta:
        verbose_name = 'Місто НП'
        verbose_name_plural = 'Міста НП'
        ordering = ['name']

    def __str__(self):
        return self.name or self.ref


class NPWarehouse(models.Model):
    ref = models.CharField('Ref', max_length=36, unique=True)
    number = models.CharField('Номер', max_length=16, blank=True, default='', db_index=True)
    number_int = models.PositiveIntegerField('Номер для сортування', null=True, blank=True)
    category = models.CharField('Категорія', max_length=32, blank=True, default='')
    type_ref = models.CharField('Тип', max_length=36, blank=True, default='')
    description = models.CharField('Опис', max_length=500, blank=True, default='')
    description_ru = models.CharField('Опис RU', max_length=500, blank=True, default='')
    short_address = models.CharField('Коротка адреса', max_length=300, blank=True, default='')
    short_address_ru = models.CharField('Коротка адреса RU', max_length=300, blank=True, default='')
    city_ref = models.CharField('Ref міста', max_length=36, blank=True, default='', db_index=True)
    city_name = models.CharField('Місто', max_length=255, blank=True, default='')
    city_name_ru = models.CharField('Місто RU', max_length=255, blank=True, default='')
    settlement_area = models.CharField('Область', max_length=255, blank=True, default='')
    settlement_region = models.CharField('Район', max_length=255, blank=True, default='')
    max_weight = models.DecimalField(
        'Макс. вага',
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField('Активне', default=True)
    is_selectable = models.BooleanField('Можна обрати', default=True)
    search_norm = models.TextField('Нормалізований пошук', blank=True, default='')
    updated_at = models.DateTimeField('Оновлено', auto_now=True)
    last_seen_sync = models.ForeignKey(
        NPSyncRun,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='warehouses',
        verbose_name='Останній синк',
    )

    class Meta:
        verbose_name = 'Відділення НП'
        verbose_name_plural = 'Відділення НП'
        indexes = [
            models.Index(fields=['city_ref', 'number'], name='np_wh_city_number_idx'),
        ]

    def __str__(self):
        label = self.number or self.ref
        if self.city_name:
            return f'№{label}, {self.city_name}'
        return f'№{label}'
