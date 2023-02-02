from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.db.models.signals import post_save
from django.dispatch import receiver
# For async tasks
from django_q.tasks import async_task, result

# Fetch Django Q models for async tasks
from django_q.models import Success, Failure, Schedule

# Local imports
from .forms import UploadFileForm
from .models import ResumeUpload, ParsedResume


# Show uploaded resumes

@login_required
def index(request):
    messages.add_message(request, messages.INFO, 'Welcome, Fucko!')
    context = {}
    user_uploads = ResumeUpload.objects.all().filter(user=request.user).values()
    context['user_uploads'] = user_uploads

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
def delete_upload(request, id):
    file = ResumeUpload.objects.all() \
        .filter(user=request.user) \
        .get(id=id)
    file.delete()
    return redirect(reverse('resume_parser:index'))


# Parse an uploaded resume
# TODO: Add async for the parsing process
@login_required
def parse_resume(request, resume_id):
    context = {}
    if ParsedResume.objects.all().filter(user=request.user, upload=resume_id).exists():
        parsed_resume = ParsedResume.objects.all().filter(user=request.user, upload=resume_id).values()
        context['parsed'] = parsed_resume

        return render(request, 'resume_parser/parsed.html', context)
    else:
        resume = ResumeUpload.objects.all().filter(id=resume_id).values()

        for r in resume:
            parse_name = request.user.id
            parse_path = r['resume']
            la_maquina = async_task('resume_parser.static.scripts.resume_parser.parser.read_resume',
                                    name=parse_name, path_name=parse_path, resume_id=resume_id,
                                    hook='resume_parser.static.scripts.resume_parser.parser.hook_after_reading')
        context['resume'] = resume

        return render(request, 'resume_parser/confirm_parse.html', context)


# Show parsed resume
@login_required
@receiver(post_save, sender=ParsedResume)
def show_parsed_resume(request, resume_id, **kwargs):
    resume = ParsedResume.objects.all().filter(user=request.user, upload=resume_id).values()
    context = {
        'resume': resume,
    }
    return render(request, 'resume_parser/parsed.html', context)
