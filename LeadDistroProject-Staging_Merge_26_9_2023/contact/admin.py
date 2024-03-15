from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import ContactUs, FeedBack

@admin.register(ContactUs)
class ContactUsAdmin(ImportExportModelAdmin): 
    list_display = ('name', 'email', 'subject', 'user_ipaddress', 'is_solved', 'timestamp',)
    list_display_links = ('name',)
    search_fields = ('name','email',)
    empty_value_display = 'Not Set'
    readonly_fields = ('user_ipaddress', 'user_os',  'timestamp',)



@admin.register(FeedBack)
class FeedBackAdmin(ImportExportModelAdmin): 
    list_display = ('name','email', 'subject', 'user_ipaddress', 'timestamp',)
    list_display_links = ('name',)
    search_fields = ('name','email',)
    empty_value_display = 'Not Set'
    readonly_fields = ('user_ipaddress', 'user_os',  'timestamp',)