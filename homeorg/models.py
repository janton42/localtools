from django.db import models

CATEGORIES = [
    ('furniture', 'furniture'),
    ('clothes', 'clothes'),
    ('sheets', 'sheets'),
    ('book', 'book'),
    ('board-game', 'board-game'),
    ('decoration', 'decoration'),
]

OWNERS = [
    ('Jeff', 'Jeff'),
    ('Marina', 'Marina'),
    ('Alex', 'Alex'),
    ('Lucas', 'Lucas'),
    ('Max', 'Max'),
    ('Anton', 'Anton'),
]


class Room(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Container(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True, related_name='containers')
    parent_container = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='subcontainers')

    def __str__(self):
        return self.name


class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    container = models.ForeignKey(Container, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True, related_name='items')
    category = models.CharField(max_length=20, choices=CATEGORIES)
    owner = models.CharField(max_length=30, choices=OWNERS)

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.container and not self.room:
            raise ValidationError('Item must be assigned to a room or a container.')

    def __str__(self):
        return self.name
