from django.urls import path

from . import views

app_name = 'informedvoter'
urlpatterns = [
    path('', views.index, name='index'),
    path('voter_info/', views.voter_info, name='voter_info'),
]
