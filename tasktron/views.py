from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from .forms import UserRegistrationForm, CompleteProfileForm,\
CreateTaskForm, UpdateTaskForm

# Import any models needed for views. Note: all views accessing db should require login
from .models import Profile, FileUpload, Task

# Import other python packages, includes ones you wrote. "script_name" is the name of the .py file
# containing ClassName, which is the desired import

# from .top_level.package_directory.script_name import ClassName

# These pages are accessible without a login.

def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method =='POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()

            messages.success(request, 'Your account has been created.\n\
            You can now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    context = {'form': form}
    return render(request, 'register.html', context)



# All views below require login
@login_required
def view_tasks(request):
    user_tasks = Task.objects.all()\
    .filter(user=request.user)\
    .values()
    completed_tasks = user_tasks.filter(status='Complete')
    ns_tasks = user_tasks.filter(status='Not Started')
    context = { 'completed_tasks': completed_tasks,
                'ns_tasks': ns_tasks
                }
    return render(request, 'view_tasks.html', context)

@login_required
def create_task(request):
    if request.method == 'POST':
        form = CreateTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            return redirect(reverse('tasktron:view_tasks'))
    else:
        form = CreateTaskForm()
    context = { 'form': form }
    return render(request, 'create_task.html', context)

@login_required
def update_task(request, id):
    task = Task.objects.all()\
    .filter(user=request.user)\
    .get(id=id)
    if request.method == 'POST':
        form = UpdateTaskForm(request.POST)
        if form.is_valid():
            task.title = form.cleaned_data['title']
            task.due = form.cleaned_data['due']
            task.status = form.cleaned_data['status']
            task.save()
            return redirect(reverse('tasktron:view_tasks'))
    else:
        form = UpdateTaskForm(initial={
                "title": task.title,
                "due": task.due,
                "status": task.status
                })
    context = { 'form': form,
                'task': task,
                }
    return render(request, 'update_task.html', context)

@login_required
def delete_task(request, id):
    task = Task.objects.all()\
    .filter(user=request.user)\
    .get(id=id)
    task.delete()
    return redirect(reverse('tasktron:view_tasks'))

@login_required
def profile_view(request):
    user_profile = Profile.objects.all()\
    .filter(user=request.user)\
    .values()
    context = { 'user_profile': user_profile }
    return render(request, 'profile_view.html', context)

@login_required
def complete_profile(request):
    if request.method == 'POST':
        form = CompleteProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect(reverse('tasktron:profile_view',pk=profile.pk))
    else:
        form = CompleteProfileForm()
    context = { 'form': form }
    return render(request, 'complete_profile.html', context)

# Upload a file
@login_required
def upload(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.user = request.user
            upload.save()
            return redirect('home')
        else:
            print(form.errors)
    else:
        form = UploadFileForm()
    context = { 'form': form }
    return render(request, 'upload.html', context)
