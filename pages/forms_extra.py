from django import forms

from config.validators import clean_person_name, clean_ua_phone
from pages.i18n_lib import tr, tr_lazy

from .models_extra import PhotoPickRequest


class CallbackForm(forms.Form):
    name = forms.CharField(
        label=tr_lazy('Імʼя'),
        max_length=120,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Олександр',
                'autocomplete': 'name',
                'data-validate': 'name',
            }
        ),
    )
    phone = forms.CharField(
        label=tr_lazy('Телефон*'),
        max_length=22,
        widget=forms.TextInput(
            attrs={
                'type': 'tel',
                'placeholder': '+38 (___) ___ - __ - __',
                'autocomplete': 'tel',
                'inputmode': 'tel',
                'data-validate': 'phone',
            }
        ),
    )
    idempotency_key = forms.CharField(widget=forms.HiddenInput(), max_length=64)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['placeholder'] = tr('Олександр')

    def clean_name(self):
        return clean_person_name(self.cleaned_data.get('name', ''), required=False)

    def clean_phone(self):
        return clean_ua_phone(self.cleaned_data.get('phone', ''))


class PhotoPickForm(forms.Form):
    phone = forms.CharField(
        label=tr_lazy('Телефон*'),
        max_length=22,
        widget=forms.TextInput(
            attrs={
                'type': 'tel',
                'placeholder': '+38 (___) ___ - __ - __',
                'autocomplete': 'tel',
                'inputmode': 'tel',
                'data-validate': 'phone',
            }
        ),
    )
    channel = forms.ChoiceField(
        label=tr_lazy('Канал звʼязку'),
        choices=PhotoPickRequest.Channel.choices,
        initial=PhotoPickRequest.Channel.CALL,
    )
    note = forms.CharField(
        label=tr_lazy('Примітка'),
        required=False,
        max_length=2000,
        widget=forms.Textarea(attrs={'rows': 3}),
    )
    idempotency_key = forms.CharField(widget=forms.HiddenInput(), max_length=64)

    def clean_phone(self):
        return clean_ua_phone(self.cleaned_data.get('phone', ''))


class InstallForm(forms.Form):
    name = forms.CharField(
        label=tr_lazy('Імʼя*'),
        max_length=120,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Олександр',
                'autocomplete': 'name',
                'data-validate': 'name',
            }
        ),
    )
    phone = forms.CharField(
        label=tr_lazy('Телефон*'),
        max_length=22,
        widget=forms.TextInput(
            attrs={
                'type': 'tel',
                'placeholder': '+38 (___) ___ - __ - __',
                'autocomplete': 'tel',
                'inputmode': 'tel',
                'data-validate': 'phone',
            }
        ),
    )
    address = forms.CharField(
        label=tr_lazy('Адреса'),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'autocomplete': 'street-address'}),
    )
    comment = forms.CharField(
        label=tr_lazy('Коментар'),
        required=False,
        max_length=2000,
        widget=forms.Textarea(attrs={'rows': 4}),
    )
    idempotency_key = forms.CharField(widget=forms.HiddenInput(), max_length=64)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['placeholder'] = tr('Олександр')

    def clean_name(self):
        return clean_person_name(self.cleaned_data.get('name', ''))

    def clean_phone(self):
        return clean_ua_phone(self.cleaned_data.get('phone', ''))
