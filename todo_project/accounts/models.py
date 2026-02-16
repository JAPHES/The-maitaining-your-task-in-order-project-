from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
    # Override default username validators so spaces/full names are allowed.
    username = models.CharField(max_length=150, unique=True)

    # here you can add any custom fields if necessary
    bio = models.TextField(null=True, blank=True)


