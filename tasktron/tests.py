from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from datetime import date
from .models import Task
from django.contrib.auth.models import User
from django.urls import reverse


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


class TaskTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.task = Task.objects.create(
            user=self.user,
            title='Test Task',
            due='2022-12-31',
            status='Not Started'
        )

    def test_create_task(self):
        """
        Test that a task can be created
        """
        self.client.login(username='testuser', password='testpassword')
        form_data = {
            'title': 'Test Task',
            'due': '2022-12-31',
            'status': 'Not Started'
        }
        response = self.client.post(reverse('tasktron:create_task'), form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.count(), 2)

    def test_view_tasks(self):
        """
        Test that the view tasks page returns the correct information
        """
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('tasktron:view_tasks'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['ns_tasks'].count(), 1)

    def test_update_task(self):
        """
        Test that a task can be updated
        """
        self.client.login(username='testuser', password='testpassword')
        form_data = {
            'title': 'Updated Test Task',
            'due': '2022-12-31',
            'status': 'In progress'
        }
        response = self.client.post(reverse('tasktron:update_task', args=[self.task.id]), form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.get(id=self.task.id).title, 'Updated Test Task')
        self.assertEqual(Task.objects.get(id=self.task.id).status, 'In progress')

    def test_delete_task(self):
        """
        Test that a task can be deleted
        """
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(reverse('tasktron:delete_task', args=[self.task.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.count(), 0)

    def test_create_task_invalid_data(self):
        """
        Test that a task cannot be created with invalid data
        """
        self.client.login(username='testuser', password='testpassword')
        form_data = {
            'title': '',  # Invalid data, title is required
            'due': '2022-12-31',
            'status': 'Not Started'
        }
        response = self.client.post(reverse('tasktron:create_task'), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.count(), 1)
        self.assertFormError(response, 'form', 'title', 'This field is required.')

    def test_create_task_unauthorized(self):
        """
        Test that an unauthorized user cannot create a task
        """
        response = self.client.post(reverse('tasktron:create_task'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.count(), 1)

    def test_view_tasks_unauthorized(self):
        """
        Test that an unauthorized user cannot view tasks
        """
        response = self.client.get(reverse('tasktron:view_tasks'))
        self.assertEqual(response.status_code, 302)

    def test_update_task_unauthorized(self):
        """
        Test that an unauthorized user cannot update a task
        """
        form_data = {
            'title': 'Updated Test Task',
            'due': '2022-12-31',
            'status': 'In progress'
        }
        response = self.client.post(reverse('tasktron:update_task', args=[self.task.id]), form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.get(id=self.task.id).title, 'Test Task')
        self.assertEqual(Task.objects.get(id=self.task.id).status, 'Not Started')

    def test_update_task_invalid_data(self):
        """
        Test that a task cannot be updated with invalid data
        """
        self.client.login(username='testuser', password='testpassword')
        form_data = {
            'title': '',  # Invalid data, title is required
            'due': '2022-12-31',
            'status': 'In progress'
        }
        response = self.client.post(reverse('tasktron:update_task', args=[self.task.id]), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.get(id=self.task.id).title, 'Test Task')
        self.assertEqual(Task.objects.get(id=self.task.id).status, 'Not Started')
        self.assertFormError(response, 'form', 'title', 'This field is required.')

    def test_delete_task_unauthorized(self):
        """
        Test that an unauthorized user cannot delete a task
        """
        response = self.client.post(reverse('tasktron:delete_task', args=[self.task.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.count(), 1)
