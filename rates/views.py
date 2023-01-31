from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, reverse
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .forms import RateRequestForm

from .models import RateRequest


class RateRequestListView(LoginRequiredMixin, ListView):
    model = RateRequest
    paginate_by = 5
    template_name = 'rates/index.html'

    def get_context_data(self, **kwargs):
        rate_estimates = self.model.objects.all().filter(user=self.request.user).values()
        context = {
            'now': timezone.now(),
            'rate_estimates': rate_estimates
        }
        return context


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
