from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import DailyLog, NotificationPreference

# Low / Mid / High dropdown choices; stored as 1, 5, 10 in DB for charts/compatibility
SYMPTOM_CHOICES = [
    ("", "Select"),
    (1, "Low"),
    (5, "Mid"),
    (10, "High"),
]

# Wellness dropdown: Good / Average / Bad; stored as 75, 50, 25 in DB (0–100)
WELLNESS_CHOICES = [
    ("", "Select"),
    (25, "Bad"),
    (50, "Average"),
    (75, "Good"),
]


class DailyLogForm(forms.ModelForm):
    """Log or update today's metrics – always saved for current user."""
    class Meta:
        model = DailyLog
        fields = [
            'cycle_day', 'steps', 'water_glasses', 'wellness_score',
            'acne_level', 'fatigue_level', 'bloating_level', 'sleep_quality',
            'weight_kg', 'mood',
        ]
        widgets = {
            'cycle_day': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 35, 'placeholder': 'e.g. 14'}),
            'steps': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'e.g. 7500'}),
            'water_glasses': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 20, 'placeholder': 'e.g. 6'}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'e.g. 64.5'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Wellness: dropdown Good / Average / Bad (stored as 75, 50, 25)
        def coerce_wellness(x):
            if x is None or x == '':
                return None
            return int(x)

        def wellness_to_choice(val):
            if val is None:
                return None
            if val <= 33:
                return 25
            if val <= 66:
                return 50
            return 75

        self.fields['wellness_score'] = forms.TypedChoiceField(
            choices=WELLNESS_CHOICES,
            coerce=coerce_wellness,
            required=False,
            empty_value=None,
            widget=forms.Select(attrs={'class': 'form-select'}),
        )
        if self.instance and getattr(self.instance, 'wellness_score') is not None:
            self.fields['wellness_score'].initial = wellness_to_choice(
                getattr(self.instance, 'wellness_score')
            )

        # Symptom and mood fields: dropdown with Select / Low / Mid / High (stored as 1, 5, 10)
        def coerce_symptom(x):
            if x is None or x == '':
                return None
            return int(x)

        def bin_to_choice(val):
            if val is None:
                return None
            if val <= 3:
                return 1
            if val <= 7:
                return 5
            return 10

        for name in ('acne_level', 'fatigue_level', 'bloating_level', 'sleep_quality', 'mood'):
            self.fields[name] = forms.TypedChoiceField(
                choices=SYMPTOM_CHOICES,
                coerce=coerce_symptom,
                required=False,
                empty_value=None,
                widget=forms.Select(attrs={'class': 'form-select'}),
            )
            if self.instance and getattr(self.instance, name) is not None:
                self.fields[name].initial = bin_to_choice(getattr(self.instance, name))

    def clean(self):
        """Ensure empty string is always None for numeric choice fields so the model gets NULL."""
        data = super().clean()
        for name in (
            'wellness_score', 'acne_level', 'fatigue_level',
            'bloating_level', 'sleep_quality', 'mood',
        ):
            if name in data and data[name] == '':
                data[name] = None
        return data


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


class NotificationPreferenceForm(forms.ModelForm):
    """Notification toggles – only for logged-in user."""

    class Meta:
        model = NotificationPreference
        fields = (
            'events_workshops', 'health_tips', 'app_updates',
            'breakfast_reminder', 'water_reminder', 'stretch_reminder', 'daily_log_reminder',
        )
        widgets = {
            'events_workshops': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'health_tips': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'app_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'breakfast_reminder': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'water_reminder': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'stretch_reminder': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'daily_log_reminder': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
