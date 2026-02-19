from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.
# THIS step should create a table task in our db where the attributes


class Task(models.Model):
    CATEGORY_PERSONAL = 'personal'
    CATEGORY_WORK = 'work'
    CATEGORY_STUDY = 'study'
    CATEGORY_HEALTH = 'health'
    CATEGORY_OTHER = 'other'
    CATEGORY_CHOICES = [
        (CATEGORY_PERSONAL, 'Personal'),
        (CATEGORY_WORK, 'Work'),
        (CATEGORY_STUDY, 'Study'),
        (CATEGORY_HEALTH, 'Health'),
        (CATEGORY_OTHER, 'Other'),
    ]

    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
    ]

    # attributes
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tasks',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_OTHER)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    is_pinned = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.completed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.completed:
            self.completed_at = None
        super().save(*args, **kwargs)


class TaskNote(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField(blank=True)
    attachment = models.FileField(upload_to='task_notes/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note for {self.task.title}"


class TaskResource(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=150)
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Resource for {self.task.title}: {self.title}"

class Book(models.Model):
    title = models.CharField(max_length=1200,unique=True)
    author = models.CharField(max_length=100)
    published_date = models.DateField()

    def __str__(self):
        return self.title
