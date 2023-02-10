from django import forms

from .models import FileUpload

class UploadFileForm(forms.ModelForm):

    class Meta:
        model = FileUpload
        fields = ['title', 'file']

class ZipcodeForm(forms.Form):
    zipcode = forms.CharField(max_length=5)

class RepLookupForm(forms.Form):
    rep = forms.CharField(max_length=100)

