from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "role", "preferred_currency")

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "role", "preferred_currency")

class UserCurrencyPreferenceForm(forms.ModelForm):
    """Form for users to change their currency preference"""
    class Meta:
        model = CustomUser
        fields = ['preferred_currency']
        widgets = {
            'preferred_currency': forms.Select(attrs={'class': 'form-select'})
        }
        labels = {
            'preferred_currency': 'Preferred Currency'
        }
        help_texts = {
            'preferred_currency': 'This will be used as the default currency in accounting forms.'
        }
