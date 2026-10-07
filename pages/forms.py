import re

from django import forms

from pages.i18n_lib import tr, tr_lazy

from .models import ContactRequest


def _topic_choices():
    return [(value, tr(label)) for value, label in ContactRequest.Topic.choices]


class ContactForm(forms.Form):
    name = forms.CharField(
        label=tr_lazy('Ім’я*'),
        max_length=120,
        widget=forms.TextInput(attrs={'placeholder': 'Олександр', 'autocomplete': 'name'}),
    )
    phone = forms.CharField(
        label=tr_lazy('Телефон*'),
        max_length=32,
        widget=forms.TextInput(
            attrs={
                'type': 'tel',
                'placeholder': '+380 00 000 00 00',
                'autocomplete': 'tel',
                'inputmode': 'tel',
            }
        ),
    )
    email = forms.EmailField(
        label=tr_lazy('Email'),
        required=False,
        widget=forms.EmailInput(
            attrs={'placeholder': 'mail@example.com', 'autocomplete': 'email'}
        ),
        error_messages={'invalid': tr_lazy('Перевірте email')},
    )
    topic = forms.ChoiceField(
        label=tr_lazy('Тема'),
        choices=_topic_choices,
        initial=ContactRequest.Topic.LOCK,
    )
    message = forms.CharField(
        label=tr_lazy('Повідомлення*'),
        widget=forms.Textarea(
            attrs={
                'rows': 5,
                'placeholder': tr_lazy(
                    'Опишіть ваше питання. Для підбору вкажіть товщину дверей або розміри A і B.'
                ),
            }
        ),
    )
    consent = forms.BooleanField(required=False)
    idempotency_key = forms.CharField(widget=forms.HiddenInput(), max_length=64)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['placeholder'] = tr('Олександр')
        self.fields['message'].widget.attrs['placeholder'] = tr(
            'Опишіть ваше питання. Для підбору вкажіть товщину дверей або розміри A і B.'
        )
        self.fields['topic'].choices = _topic_choices()

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if len(name) < 2:
            raise forms.ValidationError(tr('Вкажіть ім’я'))
        return name

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        digits = re.sub(r'\D+', '', phone)
        if len(digits) < 10:
            raise forms.ValidationError(tr('Вкажіть номер у форматі +380 00 000 00 00'))
        return phone

    def clean_message(self):
        message = self.cleaned_data['message'].strip()
        if len(message) < 10:
            raise forms.ValidationError(tr('Напишіть хоча б кілька слів (від 10 символів)'))
        return message

    def clean_consent(self):
        consent = self.cleaned_data.get('consent')
        if not consent:
            raise forms.ValidationError(tr('Потрібна згода на обробку даних'))
        return True
