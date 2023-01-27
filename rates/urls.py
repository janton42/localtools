import django.urls
from django.urls import path

from . import views

app_name = 'rates'
urlpatterns = [
    path('', views.index, name='index'),
    path('world_rates/', views.world_rates, name='world_rates'),
]