from django.db import models
from django.contrib.auth.models import User


class ResumeUpload(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=20)
    resume = models.FileField(upload_to='./resume_parser/static/uploads/')

    def __str__(self):
        return '{}: {}'.format(self.user, self.title)


# Create jobs table to handle async requests
class Job(models.Model):
    STATUSES = [
        ('PENDING', 'PENDING'),
        ('SUCCESS', 'SUCCESS'),
        ('FAILURE', 'FAILURE'),
    ]
    RESULTS = [
        (0, 'PENDING'),
        (1, 'SUCCESS'),
        (2, 'FAILURE'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUSES, default='PENDING')
    result = models.IntegerField(choices=RESULTS, default=0)

    def __str__(self):
        return '{}: {}, {}, {}'.format(self.user, self.title, self.status, self.result)


class ParsedResume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    upload = models.ForeignKey(ResumeUpload, on_delete=models.CASCADE)
    doc_line = models.IntegerField()
    line = models.CharField(max_length=1000, blank=False)
    label = models.CharField(max_length=20, blank=False)
    is_bullet = models.IntegerField(default=0)
    is_name = models.IntegerField(default=0)
    is_org = models.IntegerField(default=0)
    ents = models.IntegerField(default=0)

    def __str__(self):
        return '{}: {}, {}, {}'.format(self.user, self.upload, self.doc_line, self.line, self.label)
#