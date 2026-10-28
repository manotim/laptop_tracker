from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from .models import Laptop, Student


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


class LaptopForm(forms.ModelForm):
    class Meta:
        model = Laptop
        fields = ['owner', 'name', 'model_number', 'serial_number', 'slot_label']
        widgets = {
            'owner': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'model_number': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'slot_label': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Leave blank to use owner's admission number",
            }),
        }


class StudentCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=6,
        help_text="At least 6 characters",
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirm password",
    )

    class Meta:
        model = Student
        fields = ['admission_number', 'full_name', 'class_stream', 'email']
        widgets = {
            'admission_number': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'class_stream': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Form 4 West',
            }),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get('password'), cleaned.get('password_confirm')
        if p1 and p2 and p1 != p2:
            self.add_error('password_confirm', "Passwords do not match.")
        adm = cleaned.get('admission_number')
        if adm and Student.objects.filter(username=adm).exists():
            self.add_error('admission_number',
                           "This admission number conflicts with an existing username.")
        return cleaned

    def save(self, commit=True):
        student = super().save(commit=False)
        student.username = self.cleaned_data['admission_number']
        student.set_password(self.cleaned_data['password'])
        if commit:
            student.save()
        return student