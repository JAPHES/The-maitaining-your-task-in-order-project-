from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Help text for username
        self.fields['username'].help_text = "Required. You can choose any username you like."


        # Help text for password
        self.fields['password1'].help_text = """
            Your password must contain at least 8 characters,
            cannot be similar to personal information,
            and must include letters and numbers."""
