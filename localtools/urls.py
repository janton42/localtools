"""localtools URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from portfolio import views as portfolio_views

urlpatterns = [
    path('home-org/', include('homeorg.urls')),
    path('resume/', include('resume.urls')),
    path('userprofile/', include(('userprofile.urls', 'userprofile'), namespace='userprofile')),
    path('informedvoter/', include('informedvoter.urls')),
    path('rates/', include('rates.urls')),
    path('resume_parser/', include('resume_parser.urls')),
    path('tasktron/', include('tasktron.urls')),
    path('veteran-pers/', include(('veteran_pers.urls', 'veteran_pers'), namespace='veteran_pers')),
    path('admin/', admin.site.urls, name='admin'),
    path("__reload__/", include("django_browser_reload.urls")),
    # Portfolio last — its <slug:slug>/ pattern must not shadow the routes above
    path('', include(('portfolio.urls', 'portfolio'), namespace='portfolio')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
