from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from .forms import UserRegistrationForm, CompleteProfileForm

# Import any models needed for views. Note: all views accessing db should require login
from .models import Profile

# Import other python packages, includes ones you wrote. "script_name" is the name of the .py file
# containing ClassName, which is the desired import

# from .top_level.package_directory.script_name import ClassName

# These pages are accessible without a login.

# MOVE TO userprofile app
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
    return render(request, 'userprofile/register.html', context)

# All views below require login

# MOVE TO userprofile app
@login_required
def profile_view(request):
    user_profile = Profile.objects.all()\
    .filter(user=request.user)\
    .values()
    context = { 'user_profile': user_profile }
    return render(request, 'userprofile/profile_view.html', context)

@login_required
def complete_profile(request):
    if request.method == 'POST':
        form = CompleteProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect(reverse('userprofile:profile_view'))
    else:
        form = CompleteProfileForm()
    context = { 'form': form }
    return render(request, 'userprofile/complete_profile.html', context)

# MOVE TO fileprocessing app.
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
