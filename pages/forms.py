from django import forms

from config.validators import (
    MSG_CONSENT,
    MSG_EMAIL,
    MSG_MESSAGE,
    clean_person_name,
    clean_ua_phone,
)
from pages.i18n_lib import tr, tr_lazy

from .models import ContactRequest


def _topic_choices():
    return [(value, tr(label)) for value, label in ContactRequest.Topic.choices]


class ContactForm(forms.Form):
    name = forms.CharField(
        label=tr_lazy('Ім’я*'),
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
        error_messages={'invalid': tr_lazy(MSG_EMAIL)},
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
                'data-validate': 'message',
            }
        ),
    )
    consent = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'data-validate': 'consent'}),
    )
    idempotency_key = forms.CharField(widget=forms.HiddenInput(), max_length=64)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['placeholder'] = tr('Олександр')
        self.fields['message'].widget.attrs['placeholder'] = tr(
            'Опишіть ваше питання. Для підбору вкажіть товщину дверей або розміри A і B.'
        )
        self.fields['topic'].choices = _topic_choices()

    def clean_name(self):
        return clean_person_name(self.cleaned_data.get('name', ''))

    def clean_phone(self):
        return clean_ua_phone(self.cleaned_data.get('phone', ''))

    def clean_message(self):
        message = (self.cleaned_data.get('message') or '').strip()
        if len(message) < 10:
            raise forms.ValidationError(tr(MSG_MESSAGE))
        return message

    def clean_consent(self):
        consent = self.cleaned_data.get('consent')
        if not consent:
            raise forms.ValidationError(tr(MSG_CONSENT))
        return True
