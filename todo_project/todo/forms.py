
from django import forms
from pathlib import Path
from.models import Task, TaskNote, TaskResource

class TaskForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        text_like_fields = ['title', 'start_date', 'end_date', 'start_time', 'end_time', 'due_date']
        for field_name in text_like_fields:
            self.fields[field_name].widget.attrs.setdefault('class', 'form-control')
        self.fields['is_pinned'].widget.attrs.setdefault('class', 'form-check-input')
        self.fields['completed'].widget.attrs.setdefault('class', 'form-check-input')

    class Meta:
        model = Task
        fields = [
            'title',
            'category',
            'priority',
            'start_date',
            'end_date',
            'start_time',
            'end_time',
            'due_date',
            'is_pinned',
            'completed',
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', 'End date must be on or after the start date.')

        if (
            start_date
            and end_date
            and start_time
            and end_time
            and start_date == end_date
            and end_time <= start_time
        ):
            self.add_error('end_time', 'End time must be after start time when start and end dates are the same.')

        return cleaned_data


class TaskNoteForm(forms.ModelForm):
    MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 MB
    ALLOWED_ATTACHMENT_EXTENSIONS = {
        '.pdf', '.doc', '.docx', '.txt', '.md',
        '.jpg', '.jpeg', '.png', '.gif', '.webp',
        '.ppt', '.pptx', '.xls', '.xlsx', '.csv'
    }

    def clean(self):
        cleaned_data = super().clean()
        content = (cleaned_data.get('content') or '').strip()
        attachment = cleaned_data.get('attachment')

        if not content and not attachment:
            raise forms.ValidationError('Add note text or attach a file.')
        return cleaned_data

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if not attachment:
            return attachment

        extension = Path(attachment.name).suffix.lower()
        if extension not in self.ALLOWED_ATTACHMENT_EXTENSIONS:
            raise forms.ValidationError("File type not allowed for note attachments.")

        if attachment.size > self.MAX_ATTACHMENT_SIZE:
            raise forms.ValidationError("Attachment must be 10MB or smaller.")

        return attachment

    class Meta:
        model = TaskNote
        fields = ['content', 'attachment']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional note text...',
            }),
            'attachment': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
        }


class TaskResourceForm(forms.ModelForm):
    class Meta:
        model = TaskResource
        fields = ['title', 'url']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Resource title (e.g., Week 3 slides)',
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/resource',
            }),
        }
