from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, reverse

from .forms import RateRequestForm


@login_required
def index(request):
    return render(request, 'rates/index.html')


@login_required
def world_rates(request):
    if request.method == 'POST':
        form: RateRequestForm = RateRequestForm(request.POST)
        if form.is_valid():
            file: object = form.save(commit=False)
            file.user = request.user
            file.save()
            return redirect(reverse('resume_parser:index'))
        else:
            print(form.errors)
    else:
        form = RateRequestForm()
    context = {'form': form}
    return render(request, 'rates/index.html', context)
