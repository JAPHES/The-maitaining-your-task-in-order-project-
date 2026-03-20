from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """Custom user model with unique email and optional profile picture."""

    email = models.EmailField(unique=True)
    # Allow spaces/full names by relaxing default username validators
    username = models.CharField(max_length=150, unique=True)

    bio = models.TextField(null=True, blank=True)
    profile_pic = models.FileField(upload_to='profile_images/', null=True, blank=True)

    REQUIRED_FIELDS = ["email"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.email or self.username


