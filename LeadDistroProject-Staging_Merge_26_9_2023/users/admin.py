from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from import_export.admin import ImportExportModelAdmin

from .models import User, SuperUsers, TeamMembers, UserProfile, TextDripCampaign, LastTask, LeadsLimitRequest

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('name', 'email', 'password',  'account_type','is_dark_mode',  )}),
        ('Permissions', {'fields': (
            'last_login',
            'is_active', 
            'is_staff', 
            'is_superuser',
            'groups', 
            'user_permissions',
        )}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('name', 'email','account_type', 'password1', 'password2')

            }
        ),
    )

    list_display = ('email', 'name', 'is_staff', 'account_type', 'date_joined',)
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('email',)
    ordering = ('-date_joined',)
    filter_horizontal = ('groups', 'user_permissions',)



@admin.register(SuperUsers)
class SuperUsersAdmin(ImportExportModelAdmin):
    @admin.action(description="Team Members")
    def total_teammembers(self, obj):
        return f"{obj.count_total_team_members}"

    list_display = ('user','total_teammembers', 'company_name', 'region', 'account_type', 'created', 'updated', )
    search_fields = ('user__email', 'user__name', 'superuser_id', 'company_name', 'region', 'llr_apikey',)
    list_filter = ('account_type',)
    readonly_fields = ('superuser_id', )
    filter_horizontal = ('teams',)



@admin.register(UserProfile)
class UserProfileAdmin(ImportExportModelAdmin):
    list_display = ('user', 'api_key', 'is_td_contact', 'created', 'updated', )


@admin.register(TeamMembers)
class TeamMembersAdmin(ImportExportModelAdmin):
    list_display = ('user', 'super_users', 'all_states', 'vacation_mode', 'created', 'updated', )
    search_fields = ('user__email', 'user__name', 'team_id', 'llr_apikey',)
    readonly_fields = ('team_id', )

    def super_users(self, obj):
        return ", ".join([
            super.user.name for super in obj.team_members.all()
        ])
    super_users.short_description = "Super Users"

@admin.register(LeadsLimitRequest)
class LeadsLimitRequestAdmin(ImportExportModelAdmin):
    list_display = ('superuser' ,'team_member', 'current_limit', 'lead_limit_status', )
    search_fields = ('team_member__email',)
    list_filter = ('lead_limit_status',)

@admin.register(TextDripCampaign)
class TextDripCampaignAdmin(ImportExportModelAdmin):

    list_display = ('team_member', 'superuser', 'is_temporary_disabled', 'textdrip_compaign_value', 'assign_leads_limit', 'total_assign_leads', 'is_campaign_activated', 'created', 'updated',)
    search_fields = ('team_member__user__email', 'superuser__user__email', 'team_member__user__name', 'superuser__user__name',  'textdrip_apikey', 'textdrip_compaign_value',)
    list_filter = ('is_temporary_disabled', 'is_campaign_activated',)


@admin.register(LastTask)
class LastTaskAdmin(ImportExportModelAdmin):
    list_display = ('team_member', 'superuser', 'updated',)


from allauth.socialaccount.models import SocialToken, SocialAccount, SocialApp
admin.site.unregister(SocialToken)
admin.site.unregister(SocialAccount)
admin.site.unregister(SocialApp)

from django_celery_results.models import GroupResult, TaskResult
admin.site.unregister(GroupResult)
admin.site.unregister(TaskResult)
