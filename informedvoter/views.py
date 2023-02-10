from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse

from .forms import UploadFileForm

# Import any models needed for views. Note: all views accessing db should require login
from .models import Representative, Office, Party, District, Committee, FileUpload, Deal


# Import other python packages, includes ones you wrote. "script_name" is the name of the .py file
# containing ClassName, which is the desired import

# from .top_level.package_directory.script_name import ClassName

# These pages are accessible without a login.
@login_required
def index(request):
    offices = Office.objects.all()
    contributions = Deal.objects.all().filter(type='C')
    other_deals = Deal.objects.all().exclude(type='C')
    parties = Party.objects.all()
    committees = Committee.objects.all()
    context = {
        'offices': offices,
        'contributions': contributions,
        'parties': parties,
        'other_deals': other_deals,
        'committees': committees,
    }
    return render(request, 'informedvoter/index.html', context)


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
    context = {'form': form}
    return render(request, 'informedvoter/upload.html', context)


@login_required
def federal(request):
    offices = Office.objects.all().filter(level='F')
    parties = Party.objects.all()
    contributions = Deal.objects.all().filter(type='C')
    other_deals = Deal.objects.all().exclude(type='C')
    committees = Committee.objects.all()
    context = {
        'offices': offices,
        'parties': parties,
        'contributions': contributions,
        'other_deals': other_deals,
        'committees': committees,
    }
    return render(request, 'informedvoter/federal.html', context)


@login_required
def state(request):
    offices = Office.objects.all().filter(level='S')
    parties = Party.objects.all()
    contributions = Deal.objects.all().filter(type='C')
    other_deals = Deal.objects.all().exclude(type='C')
    committees = Committee.objects.all()
    context = {
        'offices': offices,
        'parties': parties,
        'contributions': contributions,
        'other_deals': other_deals,
        'committees': committees,
    }
    return render(request, 'informedvoter/state.html', context)


@login_required
def voter_info(request):
    return render(request, 'informedvoter/voter_info.html')
