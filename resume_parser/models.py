from django.db import models
from django.contrib.auth.models import User


class ResumeUpload(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=20)
    resume = models.FileField(upload_to='uploads/')

    def __str__(self):
        return '{}: {}'.format(self.user, self.title)
