from django import forms
from .models import Work, Applicant, WorkType


class WorkSubmissionForm(forms.Form):
    # Author / applicant info
    first_name = forms.CharField(max_length=100, label='First Name')
    last_name = forms.CharField(max_length=100, label='Last Name')
    email = forms.EmailField(label='Email')
    institution = forms.CharField(max_length=200, required=False, label='Institution')

    # Work info
    title = forms.CharField(max_length=300, label='Work Title')
    work_type = forms.ChoiceField(choices=WorkType.choices, label='Type')
    link = forms.URLField(required=False, label='Link to Work')

    def save(self):
        data = self.cleaned_data
        work = Work.objects.create(
            title=data['title'],
            work_type=data['work_type'],
            link=data.get('link', ''),
            author_first_name=data['first_name'],
            author_last_name=data['last_name'],
            institution=data.get('institution', ''),
        )
        Applicant.objects.create(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            institution=data.get('institution', ''),
            work=work,
        )
        return work
