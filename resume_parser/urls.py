from django.urls import path

from . import views

app_name = 'resume_parser'
urlpatterns = [
    path('resume_parser/', views.index, name='index'),
    path('resume_parser/upload/', views.upload, name='upload'),
    path('resume_parser/delete/<int:id>', views.delete_upload,\
     name='delete_upload'),
    path('resume_parser/parsed/<int:resume_id>', views.parse_resume,\
    name='parse')
]
