from django.urls import path
from .views import (
    CreateSuperuserDRFAPI, 
    CreateTeamMemberDRFAPI,
    LinkTeamMemberDRFAPI,
    UnlinkTeamMemberDRFAPI,
    CheckDatabaseDRFAPI, 

    CheckUserAccount, 
    CreateLeadDRFAPI,

    GenerateUserReport,
    )


app_name = "api"

urlpatterns = [
    #for admin
    path('create_superuser/', CreateSuperuserDRFAPI.as_view(), name='api_create_superuser'), 
    path('create_team_member/', CreateTeamMemberDRFAPI.as_view(), name='api_create_member'),
    path('link_team_member/', LinkTeamMemberDRFAPI.as_view(), name='api_link_member'),
    path('unlink_team_member/', UnlinkTeamMemberDRFAPI.as_view(), name='api_unlink_member'),

    path('check_user_account/', CheckUserAccount.as_view(), name='api_check_user_account'),



    #for admin | Superuser
    path('create_lead/', CreateLeadDRFAPI.as_view(), name='api_create_member'),
    path('generate_user_report/', GenerateUserReport.as_view(), name='api_generate_user_report'),


    #others
    path('check_db/', CheckDatabaseDRFAPI.as_view(), name='check_database'),

]

