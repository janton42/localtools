from django import forms
from .models import Room, Container, Item

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'description']

class ContainerForm(forms.ModelForm):
    class Meta:
        model = Container
        fields = ['name', 'description', 'room', 'parent_container']

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'description', 'container', 'room', 'category', 'owner']
