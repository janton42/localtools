import django.urls

from . import views

app_name = 'resume_parser'
urlpatterns = [
    django.urls.path('', views.index, name='index'),
    django.urls.path('upload/', views.upload, name='upload'),
    django.urls.path('delete/<int:id>', views.delete_upload, name='delete_upload'),
    # end point for parse confimration
    django.urls.path('confirm/<int:resume_id>', views.confirm_parse, name='confirm_parse'),
    django.urls.path('parsed/<int:resume_id>', views.parse_resume, name='parse'),
]

# green-yellow-muppet-video
