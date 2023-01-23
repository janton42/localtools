from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from .forms import UploadFileForm

from .models import ResumeUpload

from .local_scripts.resume_parser.parser import ResumeParser


# Show uploaded resumes

@login_required
def index(request):
    user_uploads = ResumeUpload.objects.all() \
        .filter(user=request.user) \
        .values()
    context = {
        'user_uploads': user_uploads
    }
    return render(request, 'resume_parser/index.html', context)


# Upload a file
@login_required
def upload(request):
    if request.method == 'POST':
        form: UploadFileForm = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file: object = form.save(commit=False)
            file.user = request.user
            file.save()
            return redirect(reverse('resume_parser:index'))
        else:
            print(form.errors)
    else:
        form = UploadFileForm()
    context = {'form': form}
    return render(request, 'resume_parser/upload.html', context)


# DELETE an uploaded resume
@login_required
def delete_upload(request, file_id):
    file = ResumeUpload.objects.all() \
        .filter(user=request.user) \
        .get(id=file_id)
    file.delete()
    return redirect(reverse('resume_parser:index'))


# Parse an uploaded resume
# TODO: Add async for the parsing process
@login_required
def parse_resume(request, resume_id):
    resume = ResumeUpload.objects.all() \
        .filter(id=resume_id).values()
    for r in resume:
        parser = ResumeParser(name=request.user)
        parser.get_resume_paths(r['resume'])
        status: bool = parser.say_status()
        parser.read_resume()
    context = {
        'resume': resume,
        'status': status,
    }
    return render(request, 'resume_parser/parsed.html', context)
