from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse
from django.db.models import Q

from django.utils import timezone
from django.views.generic.detail import DetailView

from .forms import UploadFileForm, ZipcodeForm, RepLookupForm

# Import any models needed for views. Note: all views accessing db should require login
from .models import Representative, Office, Party, District, Committee, FileUpload, Deal, Zipcode


# Import other python packages, includes ones you wrote. "script_name" is the name of the .py file
# containing ClassName, which is the desired import

# from .top_level.package_directory.script_name import ClassName

# These pages are accessible without a login.

@login_required
@permission_required('informedvoter.view_representative', raise_exception=True)
def index(request):
    if request.method == 'POST':
        form = ZipcodeForm(request.POST)
        if form.is_valid():
            zipcode = form.cleaned_data['zipcode']
            request.session['zipcode'] = zipcode
            links = True
            if not Zipcode.objects.filter(zipcode=zipcode).exists():
                error = 'Zipcode not found'
                explanation = 'Zipcode was either invalid, or not in our database. Please try again.'
                context = {
                    'error': error,
                    'explanation': explanation,
                }
                return render(request, 'informedvoter/error.html', context )
            context = {
                'zipcode': zipcode,
                'links': links,

            }
            return render(request, 'informedvoter/index.html', context)
        else:
            print(form.errors)
    else:
        request.session['zipcode'] = '00000'
        zip_form = ZipcodeForm()
        context = {
            'zip_form': zip_form,
        }
        return render(request, 'informedvoter/index.html', context)

@login_required
@permission_required('informedvoter.view_representative', raise_exception=True)
def overview(request):
    zipcode = request.session['zipcode']
    districts = District.objects.all().filter(zipcode__zipcode=zipcode)
    offices = Office.objects.all().filter(district__zipcode__zipcode=zipcode)
    reps = Representative.objects.all().filter(offices__district__zipcode__zipcode=zipcode)
    contributions = Deal.objects.all().filter(representative__offices__district__zipcode__zipcode=zipcode).filter(type='C')
    other_deals = Deal.objects.all().filter(representative__offices__district__zipcode__zipcode=zipcode).exclude(type='C')
    parties = Party.objects.all().filter(representative__offices__district__zipcode__zipcode=zipcode)
    committees = Committee.objects.all().filter(representative__offices__district__zipcode__zipcode=zipcode).distinct()
    context = {
        'districts': districts,
        'offices': offices,
        'reps': reps,
        'contributions': contributions,
        'parties': parties,
        'other_deals': other_deals,
        'committees': committees,
        'zipcode': zipcode,
    }
    return render(request, 'informedvoter/overview.html', context)


# Upload a file
@login_required
@permission_required('informedvoter.add_fileupload', raise_exception=True)
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
@permission_required('informedvoter.view_representative', raise_exception=True)
def federal(request):
    zipcode = request.session['zipcode']
    districts = District.objects.all().filter(zipcode__zipcode=zipcode).filter(office__level='F')
    offices = Office.objects.all().filter(district__zipcode__zipcode=zipcode).filter(level='F')
    reps = Representative.objects.all().filter(offices__district__zipcode__zipcode=zipcode).filter(offices__level='F')
    contributions = Deal.objects.all().filter(representative__offices__district__zipcode__zipcode=zipcode).filter(
        type='C').filter(representative__offices__level='F')
    other_deals = Deal.objects.all().filter(representative__offices__district__zipcode__zipcode=zipcode).exclude(
        type='C').filter(representative__offices__level='F')
    parties = Party.objects.all().filter(representative__offices__district__zipcode__zipcode=zipcode)
    committees = Committee.objects.all().filter(representative__offices__district__zipcode__zipcode=zipcode)\
        .filter(representative__offices__level='F')\
        .distinct()
    context = {
        'districts': districts,
        'offices': offices,
        'reps': reps,
        'contributions': contributions,
        'parties': parties,
        'other_deals': other_deals,
        'committees': committees,
        'zipcode': zipcode,
    }
    return render(request, 'informedvoter/federal.html', context)


@login_required
@permission_required('informedvoter.view_representative', raise_exception=True)
def state(request):
    zipcode = request.session['zipcode']
    districts = District.objects.all().filter(zipcode__zipcode=zipcode).filter(office__level='S')
    offices = Office.objects.all().filter(district__zipcode__zipcode=zipcode).filter(level='S')
    reps = Representative.objects.all().filter(offices__district__zipcode__zipcode=zipcode).filter(offices__level='S')
    contributions = Deal.objects.all().filter(representative__offices__district__zipcode__zipcode=zipcode).filter(
        type='C').filter(representative__offices__level='S')
    other_deals = Deal.objects.all().filter(representative__offices__district__zipcode__zipcode=zipcode).exclude(
        type='C').filter(representative__offices__level='S')
    parties = Party.objects.all().filter(representative__offices__district__zipcode__zipcode=zipcode)
    committees = Committee.objects.all().filter(representative__offices__district__zipcode__zipcode=zipcode)\
        .filter(representative__offices__level='S')\
        .distinct()
    context = {
        'districts': districts,
        'offices': offices,
        'reps': reps,
        'contributions': contributions,
        'parties': parties,
        'other_deals': other_deals,
        'committees': committees,
        'zipcode': zipcode,
    }
    return render(request, 'informedvoter/state.html', context)


@login_required
@permission_required('informedvoter.view_representative', raise_exception=True)
def local(request):
    zipcode = request.session['zipcode']
    districts = District.objects.all().filter(zipcode__zipcode=zipcode).filter(office__level='L')
    offices = Office.objects.all().filter(district__zipcode__zipcode=zipcode).filter(level='L')
    reps = Representative.objects.all().filter(offices__district__zipcode__zipcode=zipcode).filter(offices__level='L')
    contributions = Deal.objects.all().filter(representative__offices__district__zipcode__zipcode=zipcode).filter(
        type='C').filter(representative__offices__level='L')
    other_deals = Deal.objects.all().filter(representative__offices__district__zipcode__zipcode=zipcode).exclude(
        type='C').filter(representative__offices__level='L')
    parties = Party.objects.all().filter(representative__offices__district__zipcode__zipcode=zipcode)
    committees = Committee.objects.all().filter(representative__offices__district__zipcode__zipcode=zipcode) \
        .filter(representative__offices__level='L') \
        .distinct()
    context = {
        'districts': districts,
        'offices': offices,
        'reps': reps,
        'contributions': contributions,
        'parties': parties,
        'other_deals': other_deals,
        'committees': committees,
        'zipcode': zipcode,
    }
    return render(request, 'informedvoter/local.html', context)


@login_required
@permission_required('informedvoter.view_representative', raise_exception=True)
def voter_info(request):
    return render(request, 'informedvoter/voter_info.html')


class RepresentativeDetailView(DetailView, LoginRequiredMixin):
    model = Representative
    template_name = 'informedvoter/representative_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contributions'] = Deal.objects.all().filter(type='C')
        context['other_deals'] = Deal.objects.all().exclude(type='C')
        context['committees'] = Committee.objects.all()
        context['now'] = timezone.now()

        return context
