from django.shortcuts import render, redirect
from .models import Work
from .forms import WorkSubmissionForm


def index(request):
    return render(request, 'veteran_pers/index.html')


def works_list(request):
    works = Work.objects.filter(is_approved=True)
    return render(request, 'veteran_pers/works_list.html', {'works': works})


def submit(request):
    if request.method == 'POST':
        form = WorkSubmissionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('veteran_pers:submit_success')
    else:
        form = WorkSubmissionForm()
    return render(request, 'veteran_pers/submit.html', {'form': form})


def submit_success(request):
    return render(request, 'veteran_pers/submit_success.html')
