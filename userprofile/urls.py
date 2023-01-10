from django.urls import path

from . import views

app_name = 'userprofile'
urlpatterns = [
    path('register/', views.register, name='register'),
    path('profile/view/', views.profile_view, name='profile_view'),
    path('profile/complete/', views.complete_profile, name='complete_profile'),
]
