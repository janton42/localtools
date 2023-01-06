from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=300)

    def __str__(self):
        return '{}: {}, AKA: {}'\
        .format(\
        self.user.id,
        self.user.get_full_name(),
        self.nickname,
        )

class FileUpload(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=20)
    resume = models.FileField(upload_to='uploads/')

    def __str__(self):
        return '{}: {}'.format(self.user, self.title)

class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    due = models.DateField()
    created = models.DateField(auto_now_add=True)

    def __str__(self):
        return '{}: {}'.format(self.title, self.due)
