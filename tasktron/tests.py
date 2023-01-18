from django.test import TestCase
from django.contrib.auth.models import User
from .models import Task

class TaskModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        self.task = Task.objects.create(
            user=self.user,
            title='Test task',
            due='2022-12-31',
            status='Not Started'
        )

    def test_str_method(self):
        self.assertEqual(str(self.task), 'Test task: 2022-12-31, Not Started')

    def test_default_status(self):
        task = Task.objects.create(
            user=self.user,
            title='Another task',
            due='2022-12-31',
        )
        self.assertEqual(task.status, 'Not Started')

    def test_status_choices(self):
        task = Task(user=self.user, title='Task', due='2022-12-31', status='Complete')
        task.save()
        self.assertEqual(task.status, 'Complete')
        task.status = 'Invalid'
        self.assertRaises(ValidationError, task.full_clean)

    def test_created_date(self):
        task = Task.objects.create(
            user=self.user,
            title='Another task',
            due='2022-12-31',
        )
        self.assertIsInstance(task.created, datetime.date)
