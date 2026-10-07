import re

from django import forms

from .models import DeliveryDistrict, Order


class CheckoutForm(forms.Form):
    first_name = forms.CharField(
        label='Імʼя',
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Олександр'}),
    )
    last_name = forms.CharField(
        label='Прізвище',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Коваленко'}),
    )
    phone = forms.CharField(
        label='Телефон',
        max_length=32,
        widget=forms.TextInput(attrs={'placeholder': '+380 00 000 00 00', 'type': 'tel'}),
    )
    email = forms.EmailField(
        label='Email',
        required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'mail@example.com'}),
    )
    district = forms.ModelChoiceField(
        label='Район',
        queryset=DeliveryDistrict.objects.filter(is_active=True),
        required=False,
        empty_label='Київ — усе місто',
    )
    delivery_method = forms.ChoiceField(
        label='Доставка',
        choices=Order.DeliveryMethod.choices,
        initial=Order.DeliveryMethod.NP,
        widget=forms.HiddenInput(),
    )
    payment_method = forms.ChoiceField(
        label='Оплата',
        choices=Order.PaymentMethod.choices,
        initial=Order.PaymentMethod.COD,
        widget=forms.HiddenInput(),
    )
    address = forms.CharField(
        label='Адреса / відділення',
        max_length=300,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Відділення / адреса'}),
    )
    comment = forms.CharField(
        label='Коментар',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Коментар до замовлення'}),
    )
    idempotency_key = forms.CharField(widget=forms.HiddenInput(), max_length=64)

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        digits = re.sub(r'\D+', '', phone)
        if len(digits) < 10:
            raise forms.ValidationError('Вкажіть коректний номер телефону.')
        return phone

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get('delivery_method')
        address = (cleaned.get('address') or '').strip()
        if method in {Order.DeliveryMethod.NP, Order.DeliveryMethod.COURIER} and not address:
            self.add_error('address', 'Вкажіть адресу або відділення.')
        return cleaned
