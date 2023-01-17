from django import forms

from .models import ResumeUpload

class UploadFileForm(forms.ModelForm):

    class Meta:
        model = ResumeUpload
        fields = ['title', 'resume']
