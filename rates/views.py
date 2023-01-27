from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, reverse

from .forms import RateRequestForm

from .models import RateRequest


@login_required
def index(request):
    rate_estimates = RateRequest.objects.all().filter(user=request.user).values()
    context = {
        'rate_estimates': rate_estimates
    }
    return render(request, 'rates/index.html', context)


@login_required
def world_rates(request):
    if request.method == 'POST':
        form: RateRequestForm = RateRequestForm(request.POST)
        if form.is_valid():
            file: object = form.save(commit=False)
            file.user = request.user
            file.save()
            return redirect(reverse('rates:index'))
        else:
            print(form.errors)
    else:
        form = RateRequestForm()
    context = {'form': form}
    return render(request, 'rates/world_rates.html', context)
