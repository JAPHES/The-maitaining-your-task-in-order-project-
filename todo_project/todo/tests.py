from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import TaskForm
from .models import Task, TaskNote


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


class TaskNotesViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='owner',
            password='StrongPassword123!',
        )
        self.other_user = get_user_model().objects.create_user(
            username='other',
            password='StrongPassword123!',
        )
        self.task = Task.objects.create(
            owner=self.user,
            title='Read module notes',
        )
        TaskNote.objects.create(task=self.task, content='Remember to revise chapter 2.')

    def test_owner_can_view_task_notes_page(self):
        self.client.login(username='owner', password='StrongPassword123!')

        response = self.client.get(reverse('task_notes_view', args=[self.task.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Remember to revise chapter 2.')

    def test_non_owner_cannot_view_task_notes_page(self):
        self.client.login(username='other', password='StrongPassword123!')

        response = self.client.get(reverse('task_notes_view', args=[self.task.pk]))

        self.assertEqual(response.status_code, 404)
