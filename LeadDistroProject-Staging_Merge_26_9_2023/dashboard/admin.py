from django.contrib import admin
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportModelAdmin

from dashboard.models import (
    LeadsFile,
    LeadsFileData,
    LeadsDistribution,
    Activity,
    Tag

)



@admin.register(LeadsFile)
class LeadsFileAdmin(ImportExportModelAdmin):
    @admin.action(description="CSV File/Output")
    def originalCSVFile(self, obj):
        download_url = obj.csvfile.url
        full_url = obj.get_file_download_url()
        assigned_url = obj.get_file_download_url()
        return mark_safe(f"<a href='{download_url}'>User Uploaded</a> | <a href='{full_url}'>Complete</a>  | <a href='{assigned_url}?filter=assigned'>Assigned</a>")

    @admin.action(description="Assigned | Skipped | CallBlock")
    def leadsInfo(self, obj):
        return f"{obj.get_total_assigned_leads} | {obj.get_total_leads_skipped} | {obj.get_total_leads_callblock}"

    @admin.action(description="Allow_LLR | DNC_Block | Distribution_Block")
    def userPreference(self, obj):
        return f"{obj.is_llr_allow} | {obj.is_dnc_block} | {obj.is_distribution_block}"

    list_display = ('uid', 'user', 'status', 'total_leads','userPreference', 'leadsInfo', 'updated', 'originalCSVFile')
    readonly_fields = ('updated', 'created', 'uid', 'total_leads', 'taskid',)
    search_fields = ("user__email",)
    list_filter = ('status', 'is_dnc_block', 'is_distribution_block', )


@admin.register(LeadsFileData)
class LeadsFileDataAdmin(admin.ModelAdmin):
    list_display = ('lead_id', 'lead_file','superuser', 'name', 'phone',  'is_callblock', 'linetype', 'dnctype', 'is_ready', 'is_assigned', 'is_done', 'updated_at', )
    readonly_fields = ('lead_id',)
    search_fields = ('lead_file__uid', 'superuser__user__email', 'name', 'phone',)
    list_filter = ('is_callblock', 'linetype', 'dnctype', 'is_ready', 'is_assigned',)
    empty_value_display = 'N/A'
    date_hierarchy = 'updated_at'
    list_per_page = 100


@admin.register(LeadsDistribution)
class LeadsDistributionAdmin(admin.ModelAdmin):
    list_display = ('assign_to', 'lead', 'get_lead_info_display', 'created', )
    search_fields = ('assign_to__email', 'lead__lead_file__uid')
    list_per_page = 100


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'actions', 'description','created_at','updated_at')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('user', 'tag_name', 'created')
    search_fields = ('user__email', 'tag_name')
    list_per_page = 100