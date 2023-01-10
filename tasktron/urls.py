from django.urls import path

from . import views

app_name = 'tasktron'
urlpatterns = [
    path('tasks/', views.view_tasks, name='view_tasks'),
    path('tasks/new/', views.create_task, name='create_task'),
    path('tasks/update/<int:id>', views.update_task, name='update_task'),
    path('tasks/delete/<int:id>', views.delete_task, name='delete_task')
]
