from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import DailyLog


class DailyLogForm(forms.ModelForm):
    """Log or update today's metrics – always saved for current user."""
    class Meta:
        model = DailyLog
        fields = [
            'cycle_day', 'steps', 'wellness_score',
            'acne_level', 'fatigue_level', 'bloating_level', 'sleep_quality',
            'weight_kg', 'mood',
        ]
        widgets = {
            'cycle_day': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 35, 'placeholder': 'e.g. 14'}),
            'steps': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'e.g. 7500'}),
            'wellness_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'placeholder': '0–100'}),
            'acne_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10, 'placeholder': '1–10'}),
            'fatigue_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10, 'placeholder': '1–10'}),
            'bloating_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10, 'placeholder': '1–10'}),
            'sleep_quality': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10, 'placeholder': '1–10'}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'e.g. 64.5'}),
            'mood': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10, 'placeholder': '1–10'}),
        }


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com',
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username',
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '••••••••',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '••••••••',
        })

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken. Please choose another.')
        return username
