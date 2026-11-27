import logging

from django import forms
from django.utils.translation import get_language

from config.validators import clean_person_name, clean_ua_phone
from pages.i18n_lib import tr, tr_lazy

from .models import Order

logger = logging.getLogger(__name__)


class CheckoutForm(forms.Form):
    first_name = forms.CharField(
        label=tr_lazy('Імʼя'),
        max_length=100,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Олександр',
                'autocomplete': 'given-name',
                'data-validate': 'name',
            }
        ),
    )
    last_name = forms.CharField(
        label=tr_lazy('Прізвище'),
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Коваленко',
                'autocomplete': 'family-name',
                'data-validate': 'name-optional',
            }
        ),
    )
    phone = forms.CharField(
        label=tr_lazy('Телефон'),
        max_length=32,
        widget=forms.TextInput(
            attrs={
                'placeholder': '+38 (0__) ___ __ __',
                'type': 'tel',
                'autocomplete': 'tel',
                'inputmode': 'tel',
                'data-validate': 'phone',
            }
        ),
    )

    email = forms.EmailField(
        label=tr_lazy('Email'),
        required=False,
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'mail@example.com',
                'autocomplete': 'email',
                'data-validate': 'email',
            }
        ),
    )
    city = forms.CharField(
        label=tr_lazy('Місто'),
        max_length=120,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Київ',
                'data-validate': 'city',
                'data-np-city': '1',
                'autocomplete': 'address-level2',
            }
        ),
    )
    delivery_method = forms.ChoiceField(
        label=tr_lazy('Доставка'),
        choices=Order.DeliveryMethod.choices,
        initial=Order.DeliveryMethod.NP,
        widget=forms.HiddenInput(),
    )
    payment_method = forms.ChoiceField(
        label=tr_lazy('Оплата'),
        choices=Order.PaymentMethod.choices,
        initial=Order.PaymentMethod.CARD,
        widget=forms.HiddenInput(),
    )
    address = forms.CharField(
        label=tr_lazy('Адреса / відділення'),
        max_length=300,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': '№ відділення',
                'data-addr-input': '1',
                'data-np-warehouse': '1',
                'data-validate': 'address',
            }
        ),
    )
    np_city_ref = forms.CharField(required=False, max_length=36, widget=forms.HiddenInput())
    np_warehouse_ref = forms.CharField(required=False, max_length=36, widget=forms.HiddenInput())
    comment = forms.CharField(
        label=tr_lazy('Коментар'),
        required=False,
        max_length=4000,
        widget=forms.Textarea(
            attrs={
                'rows': 3,
                'placeholder': 'Наприклад, зручний час для дзвінка',
            }
        ),
    )
    idempotency_key = forms.CharField(widget=forms.HiddenInput(), max_length=64)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['placeholder'] = tr('Олександр')
        self.fields['last_name'].widget.attrs['placeholder'] = tr('Коваленко')
        self.fields['city'].widget.attrs['placeholder'] = tr('Київ')
        self.fields['address'].widget.attrs['placeholder'] = tr('№ відділення')
        self.fields['comment'].widget.attrs['placeholder'] = tr(
            'Наприклад, зручний час для дзвінка'
        )
        self.fields['delivery_method'].choices = [
            (v, tr(lbl)) for v, lbl in Order.DeliveryMethod.choices
        ]
        self.fields['payment_method'].choices = [
            (v, tr(lbl)) for v, lbl in Order.PaymentMethod.choices
        ]

    def clean_first_name(self):
        return clean_person_name(self.cleaned_data.get('first_name', ''))

    def clean_last_name(self):
        return clean_person_name(self.cleaned_data.get('last_name', ''), required=False)

    def clean_phone(self):
        return clean_ua_phone(self.cleaned_data.get('phone', ''))

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get('delivery_method')
        city = (cleaned.get('city') or '').strip()
        address = (cleaned.get('address') or '').strip()
        city_ref = (cleaned.get('np_city_ref') or '').strip()
        warehouse_ref = (cleaned.get('np_warehouse_ref') or '').strip()
        cleaned['city'] = city
        cleaned['address'] = address
        cleaned['np_city_ref'] = ''
        cleaned['np_warehouse_ref'] = ''
        cleaned['np_warehouse_snapshot'] = ''
        if method == Order.DeliveryMethod.NP and self._np_directory_ready():
            self._apply_np_warehouse(cleaned, city_ref, warehouse_ref)
        elif method in {Order.DeliveryMethod.NP, Order.DeliveryMethod.COURIER}:
            if not cleaned['city']:
                self.add_error('city', tr('Вкажіть місто.'))
            if not cleaned['address']:
                self.add_error('address', tr('Вкажіть адресу або відділення.'))
        if method == Order.DeliveryMethod.NP and self._np_directory_ready():
            if not cleaned.get('city'):
                self.add_error('city', tr('Вкажіть місто.'))
            if not cleaned.get('address') and 'address' not in self.errors:
                self.add_error('address', tr('Вкажіть адресу або відділення.'))
        return cleaned

    def _np_directory_ready(self) -> bool:
        if hasattr(self, '_np_ready'):
            return self._np_ready
        try:
            from novaposhta.search import has_data

            self._np_ready = bool(has_data())
        except Exception:
            logger.exception('np directory check failed')
            self._np_ready = False
        return self._np_ready

    def _apply_np_warehouse(self, cleaned, city_ref, warehouse_ref):
        from novaposhta.models import NPWarehouse
        from novaposhta.present import warehouse_public
        from novaposhta.search import EXCLUDED_CATEGORIES

        if not warehouse_ref:
            self.add_error('address', tr('Оберіть відділення зі списку'))
            return
        warehouse = (
            NPWarehouse.objects.filter(
                ref=warehouse_ref,
                is_active=True,
                is_selectable=True,
            )
            .exclude(category__in=EXCLUDED_CATEGORIES)
            .first()
        )
        if warehouse is None:
            self.add_error('address', tr('Оберіть відділення зі списку'))
            return
        if city_ref and warehouse.city_ref != city_ref:
            self.add_error('address', tr('Відділення не належить обраному місту'))
            return
        lang = (get_language() or 'ua')[:2]
        public = warehouse_public(warehouse, lang)
        cleaned['city'] = (public['city'] or cleaned.get('city') or '')[:120]
        cleaned['address'] = (public['label'] or '')[:300]
        cleaned['np_city_ref'] = warehouse.city_ref or ''
        cleaned['np_warehouse_ref'] = warehouse.ref
        cleaned['np_warehouse_snapshot'] = cleaned['address']
