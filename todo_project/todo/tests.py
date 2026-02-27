from django.test import TestCase

from .forms import TaskForm


class TaskFormValidationTests(TestCase):
    def _base_data(self):
        return {
            'title': 'Plan coursework',
            'category': 'study',
            'priority': 'medium',
            'start_date': '2026-02-10',
            'end_date': '2026-02-12',
            'start_time': '09:00',
            'end_time': '10:00',
            'due_date': '2026-02-13',
            'is_pinned': False,
            'completed': False,
        }

    def test_rejects_due_date_before_start_date(self):
        data = self._base_data()
        data['due_date'] = '2026-02-09'

        form = TaskForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn('due_date', form.errors)

    def test_rejects_due_date_before_end_date(self):
        data = self._base_data()
        data['due_date'] = '2026-02-11'

        form = TaskForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn('due_date', form.errors)

    def test_accepts_valid_date_range(self):
        form = TaskForm(data=self._base_data())

        self.assertTrue(form.is_valid())
