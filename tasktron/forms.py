from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile, FileUpload, Task

class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length = 101)
    last_name = forms.CharField(max_length = 101)
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name',\
         'email', 'password1', 'password2']

class CompleteProfileForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ['nickname']

class UploadFileForm(forms.ModelForm):

    class Meta:
        model = FileUpload
        fields = ['title', 'resume']

class CreateTaskForm(forms.ModelForm):

    class Meta:
        model = Task
        fields = ['title', 'due', 'status']
