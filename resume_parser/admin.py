from django.contrib import admin

from .models import ResumeUpload, ParsedResume

admin.site.register(ResumeUpload)
admin.site.register(ParsedResume)
