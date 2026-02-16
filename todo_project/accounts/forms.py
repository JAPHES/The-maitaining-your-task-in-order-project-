from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    # Override Django's default username validator to allow any text.
    username = forms.CharField(max_length=150)

    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Help text for username
        self.fields['username'].help_text = None

        # Help text for password
        self.fields['password1'].help_text = None
