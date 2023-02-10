from django.contrib import admin

from .models import Channel, Committee, Deal, District, FileUpload, Office, Organization, Party, Phone, Representative, \
    Url, Zipcode


class ChannelAdmin(admin.ModelAdmin):
    list_display = ('type', 'identity')
    list_filter = ('type', 'identity')
    search_fields = ('type', 'identity')
    list_per_page = 25


class CommitteeAdmin(admin.ModelAdmin):
    list_display = ('name', 'type')
    list_filter = ('name', 'type')
    search_fields = ('name', 'type')


class DealAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'description', 'organization', 'representative', 'rep_role')
    list_filter = ('title', 'description')
    search_fields = ('title', 'description')


class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_filter = ['name']
    search_fields = ['name']


class FileUploadAdmin(admin.ModelAdmin):
    list_display = ('file', 'time_stamp')
    list_filter = ('file', 'time_stamp')
    search_fields = ('file', 'time_stamp')


class OfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'level')
    list_filter = ('name', 'level')
    search_fields = ('name', 'level')


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    list_filter = ('name', 'description')
    search_fields = ('name', 'description')


class PartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation')
    list_filter = ('name', 'abbreviation')
    search_fields = ('name', 'abbreviation')


class PhoneAdmin(admin.ModelAdmin):
    list_display = ['number']
    list_filter = ['number']
    search_fields = ['number']
    list_per_page = 25


class RepresentativeAdmin(admin.ModelAdmin):
    list_filter = ('name', 'party', 'offices')
    search_fields = ('name', 'party', 'offices')


class UrlAdmin(admin.ModelAdmin):
    list_display = ('url',)
    list_filter = ('url',)
    search_fields = ('url',)
    list_per_page = 25


class ZipcodeAdmin(admin.ModelAdmin):
    list_display = ('zipcode',)
    list_filter = ('zipcode',)
    search_fields = ('zipcode',)
    list_per_page = 25


admin.site.register(Channel, ChannelAdmin)
admin.site.register(Committee, CommitteeAdmin)
admin.site.register(Deal, DealAdmin)
admin.site.register(District, DistrictAdmin)
admin.site.register(FileUpload, FileUploadAdmin)
admin.site.register(Office, OfficeAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Party, PartyAdmin)
admin.site.register(Phone, PhoneAdmin)
admin.site.register(Representative, RepresentativeAdmin)
admin.site.register(Url, UrlAdmin)
admin.site.register(Zipcode, ZipcodeAdmin)
