from django.contrib import admin

from .models import Profile, FileUpload, Task

admin.site.register(Profile)
admin.site.register(FileUpload)
admin.site.register(Task)
