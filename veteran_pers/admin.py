from django.contrib import admin
from .models import Work, Applicant


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ('title', 'work_type', 'author_last_name', 'author_first_name', 'institution', 'is_approved', 'created_at')
    list_filter = ('work_type', 'is_approved')
    search_fields = ('title', 'author_last_name', 'author_first_name', 'institution')
    list_editable = ('is_approved',)


@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'email', 'institution', 'submitted_at')
    search_fields = ('last_name', 'first_name', 'email')
