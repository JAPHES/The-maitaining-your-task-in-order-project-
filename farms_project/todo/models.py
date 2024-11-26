from django.db import models

# Create your models here.
# THIS step should create a table task in our db where the attributes


class Task(models.Model):
    # attributes
    title = models.CharField(max_length=100)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Book(models.Model):
    title = models.CharField(max_length=1200,unique=True)
    author = models.CharField(max_length=100)
    published_date = models.DateField()

    def __str__(self):
        return self.title
