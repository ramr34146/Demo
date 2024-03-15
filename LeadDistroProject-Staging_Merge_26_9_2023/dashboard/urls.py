from django.urls import path, include

from .views import (
    HomeView, 
    APIView, 
    
    AllLeadListView,
    LeadDetails,
    LeadFileDownloadView, 

    AllAPILeadListView,

    CreateLeadView,
    SelectHeadersView,
    CancelLeadView,


    TeamList,
    TeamList_LeadsLimit,
    TeamDetailView,
    LinkTeamMember,
    UnlinkTeamMember,
    DisableEnableTeamMember,
    UpdateLeadsLimitView,
    MasterReset_LeadsLimit_By_SuperUser,

    MemberLeadListView,
    AllSuperusersList,
    SendEmailLeadLimitView,

    #htmx
    HTMX_CHECK_LLR_APIKEY,
    TeamList_LeadsLimit,
    log_view,

    AllTagListView,
    CreateTagView,
    UpdateTagView,
    DeleteTagView,
    )

app_name = 'auth'


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('api/', APIView.as_view(), name='api_home'),
    path('all-leads/', AllLeadListView.as_view(), name='leads_list'),
    path('all-leads/<UID>/', LeadDetails.as_view(), name='lead_details'),
    path('all-leads/<UID>/download/', LeadFileDownloadView.as_view(), name='lead_file_download'),
    
    path('api-leads/', AllAPILeadListView.as_view(), name='api_leads_list'),

    path('upload-leads/', CreateLeadView.as_view(), name='leads_create'),
    path('upload-leads/headers/', SelectHeadersView.as_view(), name='select_headers'),
    
    path('cancel-leads/', CancelLeadView.as_view(), name='cancel_leads'),

    path('team/', TeamList.as_view(), name='team_list'),
    path('member/leadslimit', TeamList_LeadsLimit.as_view(), name='team_list_leads_limit'),
    path('member/master-reset', MasterReset_LeadsLimit_By_SuperUser.as_view(), name='super_user_master_reset_leads'),
    path('team/link/', LinkTeamMember.as_view(), name='link_team_member'),
    path('team/unlink/', UnlinkTeamMember.as_view(), name='unlink_team_member'),
    path('team/disable-enable/', DisableEnableTeamMember.as_view(), name='disable_enable_team_member'),
    path('update_leads_limit/', UpdateLeadsLimitView.as_view(), name='update_leads_limit'),

    path('team/<UID>/', TeamDetailView.as_view(), name='team_member_detail'),
    path('log_view/', log_view.as_view(), name='log_view'),


    #urls for as a members
    path('mleads/', MemberLeadListView.as_view(), name='member_leads_list'),
    path('all-superusers/', AllSuperusersList.as_view(), name='member_superuser_list'),
    path('send_email/', SendEmailLeadLimitView.as_view(), name='send_email_lead_limit'),


    #htmx urls
    path('mx-check-llr-apikey/', HTMX_CHECK_LLR_APIKEY.as_view(), name='htmx_llr_apikey'),

    #tags urls
    path('tags/', AllTagListView.as_view(), name='tags_list'),
    path('create-tag/', CreateTagView.as_view(), name='create_tags'),
    path('update-tag/', UpdateTagView.as_view(), name='update_tags'),
    path('delete-tag/', DeleteTagView.as_view(), name='delete_tags'),
]



