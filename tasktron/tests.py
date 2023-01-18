from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from datetime import date, datetime
from .models import Task
from django.contrib.auth.models import User

class TaskModelTests(TestCase):

    def test_create_task(self):
        """Test that a task can be created with a user, title, due date, and status"""
        user = User.objects.create(username='testuser')
        task = Task.objects.create(user=user, title='Test task', due='2022-01-01', status='Not Started')
        self.assertEqual(task.title, 'Test task')
        self.assertEqual(task.due, str(date(2022, 1, 1)))
        self.assertEqual(task.status, 'Not Started')

    def test_default_status(self):
        """Test that the default status is 'Not Started'"""
        user = User.objects.create(username='testuser')
        task = Task.objects.create(user=user, title='Test task', due='2022-01-01')
        self.assertEqual(task.status, 'Not Started')

    def test_valid_status(self):
        """Test that only valid statuses can be assigned to a task"""
        user = User.objects.create(username='testuser')
        task = Task.objects.create(user=user, title='Test task', due='2022-01-01')
        task.status = 'Invalid status'
        self.assertRaises(ValidationError)

    def test_string_representation(self):
        """Test that the string representation of a task is in the format 'title: due, status'"""
        user = User.objects.create(username='testuser')
        task = Task.objects.create(user=user, title='Test task', due='2022-01-01', status='Not Started')
        self.assertEqual(str(task), 'Test task: 2022-01-01, Not Started')
