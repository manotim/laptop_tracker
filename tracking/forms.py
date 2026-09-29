from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm


class StudentLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Admission Number",
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'e.g. ADM-2024-001',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Password',
        }),
    )


class CheckoutForm(forms.Form):
    duration_hours = forms.ChoiceField(
        choices=settings.SESSION_DURATION_CHOICES,
        initial=settings.DEFAULT_SESSION_HOURS,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'}),
        label="How long do you need this laptop?",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Optional — e.g. class, project',
        }),
    )