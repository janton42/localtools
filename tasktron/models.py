from django.db import models
from django.contrib.auth.models import User

class Task(models.Model):
    STATUSES = [
        ('Complete', 'Complete'),
        ('In progress', 'In progress'),
        ('On Hold','On Hold'),
        ('Not Started', 'Not Started'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    due = models.DateField()
    status = models.CharField(max_length=30, choices=STATUSES, default='Not Started')
    created = models.DateField(auto_now_add=True)

    def __str__(self):
        return '{}: {}, {}'.format(self.title, self.due, self.status)
