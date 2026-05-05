from django.shortcuts import render
from .models import Project


def index(request):
    projects = Project.objects.filter(is_published=True).order_by('order')[:12]
    return render(request, 'portfolio/index.html', {'projects': projects})
