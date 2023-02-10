from django.db import models
from django.contrib.auth.models import User


class FileUpload(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=20)
    file = models.FileField(upload_to='informedvoter/static/uploads/')
    time_stamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{}: {}'.format(self.user, self.title)


class District(models.Model):
    name = models.CharField(max_length=50)\

    def __str__(self):
        return f'{self.name}'



class Party(models.Model):
    LEANINGS = (
        ('L', 'Left'),
        ('CL', 'Center-Left'),
        ('C', 'Center'),
        ('CR', 'Center-Right'),
        ('R', 'Right'),
    )

    name = models.CharField(max_length=50, unique=True)
    abbreviation = models.CharField(max_length=10, null=True, blank=True)
    skew = models.CharField(choices=LEANINGS, max_length=2, null=True, blank=True)
    extremety = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return '{}: {}-{}'.format(self.name, self.skew, self.extremety)


class Office(models.Model):
    LEVELS = (
        ('F', 'Federal'),
        ('S', 'State'),
        ('L', 'Local'),
    )
    name = models.CharField(max_length=50)
    level = models.CharField(choices=LEVELS, max_length=2, default=None)
    district = models.ForeignKey('District', on_delete=models.SET_DEFAULT, null=True, blank=True, default=None)

    def __str__(self):
        return '{}'.format(self.name)


class Committee(models.Model):
    COMM_TYPES = (
        ('Standing', 'Standing'),
        ('Sub', 'Sub'),
        ('Select', 'Select'),
        ('Joint', 'Joint'),
        ('Whole', 'Whole'),
        ('Other', 'Other'),
    )
    name = models.CharField(max_length=50)
    description = models.TextField()
    purpose = models.TextField()
    type = models.CharField(choices=COMM_TYPES, max_length=10)

    def __str__(self):
        return '{}: {}'.format(self.name, self.type)


class Organization(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    purpose = models.TextField()

    def __str__(self):
        return '{}'.format(self.name)


class Deal(models.Model):
    ROLE_CHOICES = (
        ('G', 'Giver'),
        ('R', 'Receiver'),
    )
    DEAL_CHOICES = (
        ('C', 'Campaign Contribution'),
        ('D', 'Donation'),
        ('L', 'Loan'),
        ('S', 'Sale'),
        ('O', 'Other'),
    )
    date = models.DateField()
    amount = models.CharField(max_length=50)
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    representative = models.ForeignKey('Representative', on_delete=models.CASCADE, blank=True, default=None)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, blank=True, default=None)
    rep_role = models.CharField(choices=ROLE_CHOICES, max_length=1)
    org_role = models.CharField(choices=ROLE_CHOICES, max_length=1)
    type = models.CharField(choices=DEAL_CHOICES, max_length=1, default='C')

    def __str__(self):
        return '{}: {}'.format(self.title, self.date)


class Phone(models.Model):
    number = models.CharField(max_length=20)

    def __str__(self):
        return '{}'.format(self.number)


class Url(models.Model):
    url = models.CharField(max_length=100)

    def __str__(self):
        return '{}'.format(self.url)


class Channel(models.Model):
    type = models.CharField(max_length=50)
    identity = models.CharField(max_length=50)

    def __str__(self):
        return '{}: {}'.format(self.type, self.identity)


class Representative(models.Model):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=100, null=True, blank=True)
    party = models.ForeignKey(Party, on_delete=models.CASCADE, blank=True, default=None)
    phones = models.ManyToManyField('Phone', blank=True, default=None)
    urls = models.ManyToManyField('Url', blank=True, default=None)
    channels = models.ManyToManyField('Channel', blank=True, default=None)
    offices = models.ManyToManyField('Office', blank=True, default=None)
    committees = models.ManyToManyField('Committee', blank=True, default=None)


    def __str__(self):
        return '{} ({}) {}'.format(self.name, self.party.abbreviation, self.offices.all()[0].name
                                   )
