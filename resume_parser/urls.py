import django.urls

from . import views

app_name = 'resume_parser'
urlpatterns = [
    django.urls.path('resume_parser/', views.index, name='index'),
    django.urls.path('resume_parser/upload/', views.upload, name='upload'),
    django.urls.path('resume_parser/delete/<int:id>', views.delete_upload, name='delete_upload'),
    # end point for parse confimration
    django.urls.path('resume_parser/confirm/<int:resume_id>', views.confirm_parse, name='confirm_parse'),
    django.urls.path('resume_parser/parsed/<int:resume_id>', views.parse_resume, name='parse'),
]
