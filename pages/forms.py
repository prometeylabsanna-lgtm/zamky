import re

from django import forms

from .models import ContactRequest


class ContactForm(forms.Form):
    name = forms.CharField(
        label='Ім’я*',
        max_length=120,
        widget=forms.TextInput(attrs={'placeholder': 'Олександр', 'autocomplete': 'name'}),
    )
    phone = forms.CharField(
        label='Телефон*',
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
        label='Email',
        required=False,
        widget=forms.EmailInput(
            attrs={'placeholder': 'mail@example.com', 'autocomplete': 'email'}
        ),
        error_messages={'invalid': 'Перевірте email'},
    )
    topic = forms.ChoiceField(
        label='Тема',
        choices=ContactRequest.Topic.choices,
        initial=ContactRequest.Topic.LOCK,
    )
    message = forms.CharField(
        label='Повідомлення*',
        widget=forms.Textarea(
            attrs={
                'rows': 5,
                'placeholder': 'Опишіть ваше питання. Для підбору вкажіть товщину дверей або розміри A і B.',
            }
        ),
    )
    consent = forms.BooleanField(required=False)
    idempotency_key = forms.CharField(widget=forms.HiddenInput(), max_length=64)

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if len(name) < 2:
            raise forms.ValidationError('Вкажіть ім’я')
        return name

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        digits = re.sub(r'\D+', '', phone)
        if len(digits) < 10:
            raise forms.ValidationError('Вкажіть номер у форматі +380 00 000 00 00')
        return phone

    def clean_message(self):
        message = self.cleaned_data['message'].strip()
        if len(message) < 10:
            raise forms.ValidationError('Напишіть хоча б кілька слів (від 10 символів)')
        return message

    def clean_consent(self):
        consent = self.cleaned_data.get('consent')
        if not consent:
            raise forms.ValidationError('Потрібна згода на обробку даних')
        return True
