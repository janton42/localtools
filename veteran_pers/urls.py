from django.urls import path
from . import views

app_name = 'veteran_pers'

urlpatterns = [
    path('', views.index, name='index'),
    path('works/', views.works_list, name='works_list'),
    path('submit/', views.submit, name='submit'),
    path('submit/success/', views.submit_success, name='submit_success'),
]
