from django.urls import path

from . import views

app_name = 'tasktron'
urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload, name='upload'),
    path('profile/view/', views.profile_view, name='profile_view'),
    path('profile/complete/', views.complete_profile, name='complete_profile'),
    path('tasks/', views.view_tasks, name='view_tasks'),
    path('tasks/new/', views.create_task, name='create_task'),
]
