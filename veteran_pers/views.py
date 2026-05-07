from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import Work, Applicant, ReviewStatus
from .forms import WorkSubmissionForm, ReviewForm


def reviewer_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            try:
                if not request.user.profile.is_reviewer:
                    raise PermissionDenied
            except AttributeError:
                raise PermissionDenied
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


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


@reviewer_required
def review_queue(request):
    pending = Applicant.objects.filter(status=ReviewStatus.PENDING).select_related('work')
    approved = Applicant.objects.filter(status=ReviewStatus.APPROVED).select_related('work')
    denied = Applicant.objects.filter(status=ReviewStatus.DENIED).select_related('work')
    return render(request, 'veteran_pers/review_queue.html', {
        'pending': pending,
        'approved': approved,
        'denied': denied,
    })


@reviewer_required
def review_applicant(request, pk):
    applicant = get_object_or_404(Applicant, pk=pk)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            old_status = applicant.status
            applicant.status = form.cleaned_data['decision']
            applicant.reviewer_notes = form.cleaned_data['justification']
            # Sync is_approved on the work
            applicant.work.is_approved = (applicant.status == ReviewStatus.APPROVED)
            applicant.work.save()
            applicant.save()
            return redirect('veteran_pers:review_queue')
    else:
        # Pre-populate form if already reviewed
        initial = {}
        if applicant.status != ReviewStatus.PENDING:
            initial = {'decision': applicant.status, 'justification': applicant.reviewer_notes}
        form = ReviewForm(initial=initial)
    return render(request, 'veteran_pers/review_applicant.html', {'applicant': applicant, 'form': form})


