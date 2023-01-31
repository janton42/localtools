from django.urls import path

from .views import RateRequestListView
from . import views

app_name = 'rates'
urlpatterns = [
    path('', RateRequestListView.as_view(), name='index'),
    path('world_rates/', views.world_rates, name='world_rates'),
]