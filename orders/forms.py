import re

from django import forms

from pages.i18n_lib import tr, tr_lazy

from .models import DeliveryDistrict, Order


class CheckoutForm(forms.Form):
    first_name = forms.CharField(
        label=tr_lazy('Імʼя'),
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Олександр'}),
    )
    last_name = forms.CharField(
        label=tr_lazy('Прізвище'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Коваленко'}),
    )
    phone = forms.CharField(
        label=tr_lazy('Телефон'),
        max_length=32,
        widget=forms.TextInput(attrs={'placeholder': '+380 00 000 00 00', 'type': 'tel'}),
    )
    email = forms.EmailField(
        label=tr_lazy('Email'),
        required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'mail@example.com'}),
    )
    city = forms.CharField(
        label=tr_lazy('Місто'),
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Київ'}),
    )
    district = forms.ModelChoiceField(
        label=tr_lazy('Район'),
        queryset=DeliveryDistrict.objects.filter(is_active=True),
        required=False,
        empty_label=tr_lazy('Київ — усе місто'),
        widget=forms.HiddenInput(),
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
            }
        ),
    )
    comment = forms.CharField(
        label=tr_lazy('Коментар'),
        required=False,
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
        self.fields['district'].empty_label = tr('Київ — усе місто')
        self.fields['delivery_method'].choices = [
            (v, tr(lbl)) for v, lbl in Order.DeliveryMethod.choices
        ]
        self.fields['payment_method'].choices = [
            (v, tr(lbl)) for v, lbl in Order.PaymentMethod.choices
        ]

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        digits = re.sub(r'\D+', '', phone)
        if len(digits) < 10:
            raise forms.ValidationError(tr('Вкажіть коректний номер телефону.'))
        return phone

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get('delivery_method')
        city = (cleaned.get('city') or '').strip()
        address = (cleaned.get('address') or '').strip()
        cleaned['city'] = city
        cleaned['address'] = address
        if method in {Order.DeliveryMethod.NP, Order.DeliveryMethod.COURIER}:
            if not city:
                self.add_error('city', tr('Вкажіть місто.'))
            if not address:
                self.add_error('address', tr('Вкажіть адресу або відділення.'))
        return cleaned
