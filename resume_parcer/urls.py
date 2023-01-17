from django.urls import path

from . import views

app_name = 'resume_parcer'
urlpatterns = [
    path('resume_parcer/', views.index, name='index'),
    path('resume_parcer/upload/', views.upload, name='upload'),
    path('resume_parcer/delete/<int:id>', views.delete_upload,\
     name='delete_upload')

]
