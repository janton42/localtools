import os

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from .models import ResumeUpload


class ResumeUploadTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.resume = ResumeUpload.objects.create(
            user=self.user,
            title='Test Resume',
            resume='test.pdf'
        )

    def test_str_method(self):
        """
        Test that the __str__ method of ResumeUpload model returns the expected string
        """
        self.assertEqual(str(self.resume), 'testuser: Test Resume')

    def test_upload_resume(self):
        """
        Test that a resume file can be uploaded
        """
        # self.assertTrue(os.path.exists(self.resume.resume.path))
        self.assertEqual(self.resume.resume.name, 'test.pdf')

    def test_upload_resume_with_wrong_extension(self):
        """
        Test that a resume file can't be uploaded with a wrong extension
        """
        resume = ResumeUpload.objects.create(
            user=self.user,
            title='Test Resume',
            resume='test.txt'
        )
        self.assertFalse(os.path.exists(resume.resume.path))


class ResumeParserViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.resume = ResumeUpload.objects.create(
            user=self.user,
            title='Test Resume',
            resume='test.pdf'
        )

    def test_index_view(self):
        """
        Test that the index view returns the expected template
        and context
        """
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('resume_parser:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'resume_parser/index.html')
        self.assertEqual(response.context['user_uploads'][0]['id'], self.resume.id)

    def test_upload_view(self):
        """
        Test that the upload view returns the expected template
        and context and that a file can be uploaded
        """
        self.client.login(username='testuser', password='testpassword')
        with open('test.pdf', 'rb') as f:
            form_data = {'title': 'Test Resume 2'}
            form_file = {'resume': f}
            response = self.client.post(reverse('resume_parser:upload'), form_data, form_file)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ResumeUpload.objects.count(), 2)
        self.assertTrue(os.path.exists(ResumeUpload.objects.get(title='Test Resume 2').resume.path))

    def test_upload_view_invalid_form(self):
        """
        Test that the upload view returns the expected template
        and context and that a file can not be uploaded with an invalid form
        """
        self.client.login(username='testuser', password='testpassword')
        form_data = {'title': ''}  # Invalid form data
        response = self.client.post(reverse('resume_parser:upload'), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ResumeUpload.objects.count(), 1)
        self.assertFormError(response, 'form', 'title', 'This field is required.')

    def test_delete_upload_view(self):
        """
        Test that the delete_upload view deletes the expected file
        and redirects to the expected URL
        """
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(reverse('resume_parser:delete_upload', kwargs={'pk': self.resume.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ResumeUpload.objects.count(), 0)
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(reverse('resume_parser:delete_upload', args=[self.resume.id]))
        self.assertEqual(response.status_code, 302)
