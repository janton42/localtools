from django.urls import path

from . import views

app_name = 'informedvoter'
urlpatterns = [
    path('', views.index, name='index'),
    path('voter_info/', views.voter_info, name='voter_info'),
    path('federal/', views.federal, name='federal'),
    path('state/', views.state, name='state'),
    path('local/', views.local, name='local'),
    path('representative/<int:pk>/', views.RepresentativeDetailView.as_view(), name='representative_detail'),
    path('Overview/', views.overview, name='overview'),
]
