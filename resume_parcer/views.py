from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from .forms import UploadFileForm

from .models import ResumeUpload

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
    uploade.delete()
    return redirect(reverse('resume_parcer:index'))
