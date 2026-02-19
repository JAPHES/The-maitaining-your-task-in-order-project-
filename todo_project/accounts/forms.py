from django.contrib.auth.forms import UserCreationForm
from django import forms
from pathlib import Path
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


class CustomUserProfileForm(forms.ModelForm):
    MAX_PROFILE_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

    def clean_profile_image(self):
        profile_image = self.cleaned_data.get("profile_image")
        if not profile_image:
            return profile_image

        extension = Path(profile_image.name).suffix.lower()
        if extension not in self.ALLOWED_IMAGE_EXTENSIONS:
            raise forms.ValidationError("Only image files are allowed: jpg, jpeg, png, gif, webp.")

        if profile_image.size > self.MAX_PROFILE_IMAGE_SIZE:
            raise forms.ValidationError("Profile image must be 5MB or smaller.")

        return profile_image

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "email", "bio", "profile_image"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "profile_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
