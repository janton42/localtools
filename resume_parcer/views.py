from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from .forms import UploadFileForm

from .models import ResumeUpload

from .local_scripts.resume_parser.parser import ResumeParser

# Show uploaded resumes
@login_required
def index(request):
    user_uploads = ResumeUpload.objects.all()\
    .filter(user=request.user)\
    .values()
    context = {
        'user_uploads': user_uploads
                }
    return render(request, 'resume_parcer/index.html', context)

# Upload a file
@login_required
def upload(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.user = request.user
            upload.save()
            return redirect(reverse('resume_parcer:index'))
        else:
            print(form.errors)
    else:
        form = UploadFileForm()
    context = { 'form': form }
    return render(request, 'resume_parcer/upload.html', context)


# DELETE an uploaded resume
@login_required
def delete_upload(request, id):
    upload = ResumeUpload.objects.all()\
    .filter(user=request.user)\
    .get(id=id)
    upload.delete()
    return redirect(reverse('resume_parcer:index'))


# Parse an uploaded resume
@login_required
def parse_resume(request, resume_id):
    resume = ResumeUpload.objects.all()\
    .filter(user=request.user)\
    .get(id=resume_id)\
    .values()
    for r in resume:
        # Initialize a parcer instance named after the current user
        parser = ResumeParser(name=request.user)
        # Make a folder for this user, if one doesn't already exist,
        # get the full path to the selected resume file to be parsed,
        # and get the uploaded file's extension
        parser.get_resume_paths(r['resume'])
        status = parser.say_status()
        parser.read_resume()
    context = {
        'resume': resume,
        'status': status
    }
    return render(request, 'parsed.html', context)
