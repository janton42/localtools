from django.contrib.auth.models import User
from django.db import models

from .choices import ZONES, LEVELS


class Skill(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.name}'


class Country(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=2)
    zone = models.CharField(max_length=1,
                            choices=ZONES)

    def __str__(self):
        return f'{self.code}, {self.name}, {self.zone}'


class RateRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    level = models.IntegerField(choices=LEVELS)
    employer_country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='employer_country')
    worker_country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='worker_country')
    rate = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    time_stamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.skill}, {self.level}, {self.employer_country}, {self.worker_country}, ' \
               f'{self.rate}, {self.time_stamp}'


class RateResponse(models.Model):
    rate_request = models.ForeignKey(RateRequest, on_delete=models.CASCADE)
    highest_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    median_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    lowest_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    time_stamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.rate_request}, {self.lowest_rate}, {self.time_stamp}'
