from django.shortcuts import render, get_object_or_404
from .models import Project, Tag


def index(request):
    qs = Project.objects.filter(is_published=True).order_by('order')

    tag = request.GET.get('tag')
    date = request.GET.get('date')

    if tag:
        qs = qs.filter(tags__slug=tag)
    if date:
        # Expecting YYYY-MM-DD from a date input
        qs = qs.filter(project_date=date)

    projects = qs[:12]
    tags = Tag.objects.all()
    return render(request, 'portfolio/index.html', {'projects': projects, 'tags': tags, 'selected_tag': tag, 'selected_date': date})


def detail(request, slug):
    project = get_object_or_404(Project, slug=slug, is_published=True)
    return render(request, 'portfolio/detail.html', {'project': project})
