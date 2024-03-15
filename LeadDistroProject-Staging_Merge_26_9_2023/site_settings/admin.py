from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from site_settings.models import GeneralSettings


@admin.register(GeneralSettings)
class GeneralSettingsAdmin(ImportExportModelAdmin):
    list_display = ('pk', 'is_maintenance_mode', 'updated', )
    fieldsets = (
        ('Maintenance Mode Settings', {'fields':('is_maintenance_mode', 
                                     )}),
    )

    def has_add_permission(self, request):
        count = GeneralSettings.objects.all().count()
        if count == 0:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        return False


