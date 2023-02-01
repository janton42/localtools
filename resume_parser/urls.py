from django.urls import path

from . import views

app_name = 'resume_parser'
urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload, name='upload'),
    path('delete/<int:id>', views.delete_upload, name='delete_upload'),
    # end point for parse confimration
    path('confirm_parse/<int:resume_id>', views.parse_resume, name='parse'),
    path('parsed/<int:task_id>', views.show_parsed_resume, name='parsed')
]

# green-yellow-muppet-video
