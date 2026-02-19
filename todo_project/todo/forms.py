
from django import forms
from.models import Task

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
