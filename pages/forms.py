from django import forms
from django.utils.translation import get_language

from config.validators import (
    MSG_CONSENT,
    MSG_EMAIL,
    MSG_MESSAGE,
    clean_person_name,
    clean_ua_phone,
)
from pages.contact_form_cms import get_contact_form_copy
from pages.i18n_lib import tr, tr_lazy

from .models import ContactRequest


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
        max_length=32,
        widget=forms.TextInput(
            attrs={
                'type': 'tel',
                'placeholder': '+38 (0__) ___ __ __',
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
                'placeholder': '',
                'autocomplete': 'email',
                'data-validate': 'email',
            }
        ),
        error_messages={'invalid': tr_lazy(MSG_EMAIL)},
    )
    topic = forms.ChoiceField(
        label=tr_lazy('Тема'),
        choices=ContactRequest.Topic.choices,
        initial=ContactRequest.Topic.LOCK,
    )
    message = forms.CharField(
        label=tr_lazy('Повідомлення*'),
        max_length=4000,
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

    def __init__(self, *args, lang=None, **kwargs):
        super().__init__(*args, **kwargs)
        raw = lang if lang is not None else (get_language() or 'ua')
        copy = get_contact_form_copy(raw)
        self.fields['name'].label = copy['name_label']
        self.fields['name'].widget.attrs['placeholder'] = copy['name_ph']
        self.fields['phone'].label = copy['phone_label']
        self.fields['phone'].widget.attrs['placeholder'] = copy['phone_ph']
        self.fields['email'].label = copy['email_label']
        self.fields['email'].widget.attrs['placeholder'] = copy['email_ph']
        self.fields['topic'].label = copy['topic_label']
        self.fields['topic'].choices = copy['topics']
        self.fields['message'].label = copy['message_label']
        self.fields['message'].widget.attrs['placeholder'] = copy['message_ph']
        self.contact_copy = copy

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
