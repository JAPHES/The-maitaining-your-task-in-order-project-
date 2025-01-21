from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
    # here you can add any custom fields if necessary
    bio = models.TextField(null=True, blank=True)


