from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from datetime import datetime

from .forms import CreateTaskForm, UpdateTaskForm

# Import any models needed for views. Note: all views accessing db should require login
from .models import Task


# Import other python packages, includes ones you wrote. "script_name" is the name of the .py file
# containing ClassName, which is the desired import

# from .top_level.package_directory.script_name import ClassName

# These pages are accessible without a login.

# All views below require login

# CREATE an item in the db
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
    context = {'form': form}
    return render(request, 'tasktron/create_task.html', context)


# READ items in the db
@login_required
def view_tasks(request):
    t = datetime.date(datetime.now()).isoformat()
    user_tasks = Task.objects.all() \
        .filter(user=request.user) \
        .values()
    completed_tasks = user_tasks.filter(status='Complete')
    ns_tasks = user_tasks.filter(status='Not Started')
    ip_tasks = user_tasks.filter(status='In progress')
    oh_tasks = user_tasks.filter(status='On Hold')
    tc_tasks = user_tasks.filter(due=t, status='Complete')
    td_tasks = user_tasks.filter(due=t).exclude(status='Complete')
    context = {'completed_tasks': completed_tasks,
               'ns_tasks': ns_tasks,
               'ip_tasks': ip_tasks,
               'oh_tasks': oh_tasks,
               'tc_tasks': tc_tasks,
               'td_tasks': td_tasks,
               }
    return render(request, 'tasktron/view_tasks.html', context)


# UPDATE an item in the db
@login_required
def update_task(request, id):
    task = Task.objects.all() \
        .filter(user=request.user) \
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
    context = {'form': form,
               'task': task,
               }
    return render(request, 'tasktron/update_task.html', context)


# DELETE an item from the db
@login_required
def delete_task(request, id):
    task = Task.objects.all() \
        .filter(user=request.user) \
        .get(id=id)
    task.delete()
    return redirect(reverse('tasktron:view_tasks'))
