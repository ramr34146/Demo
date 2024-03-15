from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.paginator import Paginator

from django.contrib.auth import get_user_model
UserModel = get_user_model()

#non django 
from itertools import cycle
from concurrent import futures
from functools import reduce

#custom
from utils.utils import is_valid_uuid
from utils.handle_usha import USHA
from utils.handle_llr import LandlineRemoverAPI
from dashboard.models import LeadsFile, LeadsFileData, LeadsDistribution
from users.models import SuperUsers, TeamMembers, LastTask, TextDripCampaign, UserProfile
from allauth.account.admin import EmailAddress
from django.forms.models import model_to_dict
from utils.handle_textdrip import TextDrip
textdrip_obj = TextDrip()

# from utils.handle_llr_bulk import API_LLR_BULK
from utils.handle_llr_bulk_oneapi import API_LLR_BULK_1API
from utils.handle_usha_bulk import API_USHA_BULK
from utils.handle_llr_bulklist import API_LLR_BULK_LIST
from utils.handle_states import get_clean_state 
from utils.handle_db_objects import checkAgentLeadAlreadyExist
from utils.handle_email import (
    InvalidCampaignAlertSuperUserSendEmail ,
    InvalidCampaignAlertTeamMemberSendEmail
    )

def returnLLREmptyData(phone_numbers):
    data = {}
    for number in phone_numbers:
        data.update({number:['','']})
    return data

def returnUSHAEmptyData(phone_numbers):
    data = {}
    for number in phone_numbers:
        data.update({number:False})
    return data



#functional method - imp
def UpdateLeadsPhoneDataTypes(leadfile_uid):
    """
        # method to handle phone type data and updating lead file data object
        # with having linetype, dnctype, is_callblock, is_ready to assign
        # calling in celery_tasks.py |     
    """
    lead_file_obj = LeadsFile.objects.get(uid=leadfile_uid)
    leadsfiledata_qs = lead_file_obj.return_leadsfiledata_qs()
    lead_file_user = lead_file_obj.get_superuser_obj()
    #apikeys = returnLLRAPIkeys(superuser_obj=lead_file_user)
    is_llr_allow = lead_file_obj.is_llr_allow
    if is_llr_allow:
        llr_apikey = lead_file_user.llr_apikey
        llr_apikey_validity = is_llr_apikey_valid(llr_apikey)
    else:
        llr_apikey = None
        llr_apikey_validity = False
    
  

    #start - sending request to check auto topup
    try: 
        if is_llr_allow == True and llr_apikey_validity == True:
            LandlineRemoverAPI().handleAutoTopUp(apikey=llr_apikey, total_leads=int(leadsfiledata_qs.count()))
    except: pass
    #end - sending request to check auto topup

    usha_bulk_api_obj = API_USHA_BULK()
    paginator = Paginator(leadsfiledata_qs, 250)

    for page in range(1, paginator.num_pages+1):
        update_objs = []
        objects_list = paginator.page(page).object_list
        phone_numbers = list(objects_list.values_list('phone', flat=True)) #[row.phone for row in objects_list] 
        # print(phone_numbers)

        if llr_apikey is not None and is_llr_allow == True and llr_apikey_validity == True:
            llr_bulk_api_obj = API_LLR_BULK_LIST(apikey=llr_apikey, numbers_list=phone_numbers)
            llr_data = llr_bulk_api_obj.BulkList_GetNumbersData()
        else:
            llr_data = returnLLREmptyData(phone_numbers)
        # print(llr_data)

        if lead_file_user.is_usha_account():
            usha_data = usha_bulk_api_obj.GetNumbersData(phone_numbers)
        else:
            usha_data = returnUSHAEmptyData(phone_numbers)
        # print(usha_data)

        for object in objects_list:
            if object.is_ready == False:
                clean_phone = object.phone
                object.linetype, object.dnctype = llr_data.get(clean_phone, ["",""])
                object.is_callblock = usha_data.get(clean_phone, False)
                object.is_ready = True
            update_objs.append(object)
        
        if len(update_objs) > 0:
            LeadsFileData.objects.bulk_update(update_objs, ['linetype', 'dnctype', 'is_callblock', 'is_ready'])
    return None 



#functional method - imp
def AssignTasks(leadfile_uid=None):
    lead_file_obj = LeadsFile.objects.get(uid=leadfile_uid)
    leadsfiledata_qs = lead_file_obj.return_total_assigned_leads()  # return_leadsfiledata_qs()
    superuser_obj = lead_file_obj.get_superuser_obj()
    team_members_qs = superuser_obj.teams.all().filter(team_id__in=lead_file_obj.return_team_ids_list(),textdripcampaign__is_campaign_activated=True).order_by('pk')

    no_of_agents = team_members_qs.count()
    # print(no_of_agents)
    if no_of_agents == 0:
        return True

    # dict of list to handle team leads limit and at the end update database
    team_limits = {}
    for teamlimit in team_members_qs:
        team_limits[str(teamlimit.team_id)] = teamlimit.campaign_data().assign_leads_limit

    # getting member obj who got last task
    lasttask_member_obj = LastTask.objects.filter(superuser__user=lead_file_obj.user)
    if lasttask_member_obj:
        lasttask_member_obj = lasttask_member_obj.first()

        # making teams objects iterable
    teams = cycle(team_members_qs)

    if lasttask_member_obj:
        for i in range(team_members_qs.count()):
            team_member_obj = next(teams)
            if team_member_obj.team_id == lasttask_member_obj.team_member.team_id:  # type: ignore
                break

    tasks_obj_list = []
    leadsdata_update_obj_list = []  # only to update task is assigned

    # team_list = [next(teams) for _ in range(no_of_agents)]

    for task in leadsfiledata_qs:
        task_state = get_clean_state(task.state)
        # print(task, task_state)
        task_assigned = False
        for i in range(no_of_agents):
            team_member_obj = next(teams)
            team_id = str(team_member_obj.team_id)
            leads_limit = team_limits.get(team_id, 0)
            all_status_allow = team_member_obj.all_states
            states_list = team_member_obj.states_list

            is_state_match_with_agent = states_list.get(task_state, False)
            if is_state_match_with_agent is not False: is_state_match_with_agent = True

            agent_already_checked = checkAgentLeadAlreadyExist(task.phone,
                                                               team_member_obj.user,
                                                               superuser_obj
                                                               )
            # print(task, task_state, team_member_obj, all_status_allow, is_state_match_with_agent, agent_already_checked)

            if agent_already_checked:
                pass

            elif (leads_limit == -1 or leads_limit > 0) and (all_status_allow or is_state_match_with_agent):
                # print("if conidtion triggered")
                tasks_obj_list.append(LeadsDistribution(assign_to=team_member_obj.user, lead=task))
                task.is_assigned = True
                leadsdata_update_obj_list.append(task)
                if leads_limit > 0:
                    team_limits[team_id] += -1
                break

                # update remaining limits of members in campaign table
    campaign_update_objects = []
    campaign_members_qs = TextDripCampaign.objects.filter(team_member__team_id__in=list(team_limits.keys()))
    for campaign_obj in campaign_members_qs:
        campaign_obj.assign_leads_limit = team_limits.get(str(campaign_obj.team_member.team_id), -1)
        campaign_update_objects.append(campaign_obj)
    if len(campaign_update_objects) > 0:
        TextDripCampaign.objects.bulk_update(campaign_update_objects, ['assign_leads_limit'])

    if len(tasks_obj_list) > 0:
        LeadsDistribution.objects.bulk_create(tasks_obj_list, ignore_conflicts=True, batch_size=500)
        LeadsFileData.objects.bulk_update(leadsdata_update_obj_list, ['is_assigned'])

    if lasttask_member_obj:
        lasttask_member_obj.team_member = team_member_obj  # type: ignore
        lasttask_member_obj.save()  # type: ignore
    else:
        LastTask.objects.create(team_member=team_member_obj, superuser=superuser_obj)  # type: ignore

    teams = tasks_obj_list = leadsfiledata_qs = team_members_qs = None  # for clearning memory
    return None


#helping function - in action
def CheckEmailExist(email):
    if UserModel.objects.filter(email=email).exists():
        return True 
    else:
        return False
    
#helping function - in action
def returnLLRAPIkeys(user_obj=None, superuser_obj=None):
    api_keys = []
    if user_obj is not None:
        super_user = SuperUsers.objects.get(user=user_obj)
    else:
        super_user = superuser_obj
    if super_user.llr_apikey: # type: ignore
        api_keys.append(super_user.llr_apikey) # type: ignore
    team_apikeys =list(set([api['llr_apikey'] for api in super_user.teams.all().values('llr_apikey') if api['llr_apikey']]))  # type: ignore
    api_keys.extend(team_apikeys)
    if len(api_keys) > 0:
        return api_keys
    return None


#function for sending email on invitation - working fine
def SendInvitationEmailToMember(data):
    superuser_name = data.get('superuser_name', '')
    member_email = data.get('member_email','')
    superuser_id = data.get('superuser_id','')
    member_id = data.get('member_id','')
    redirect_url = data.get('redirect_url')
    context = {'superuser' : superuser_name,}
    
    context['invitation_link'] =  f"https://app.textdrip.com/tauth?redirect=https%3A%2F%2F{redirect_url}%2Fmember-process%2F%3Fmid%3D{member_id}%26sid%3D{superuser_id}"

    subject = f'Invitation: You Got an Invitation From {superuser_name}'
    html_message = render_to_string('pages/mail.html', context)
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, plain_message, from_email, [member_email], html_message=html_message, fail_silently=False)

#function for Team Member Accept Invitation
def TeamMemberAcceptInvitation(superuser_email,team_email):

    context = {'team_email': team_email, }

    subject = f'Invitation: Team Member Accept Invitation'
    html_message = render_to_string('pages/accept_invite.html', context)
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, plain_message, from_email, [superuser_email], html_message=html_message, fail_silently=False)

#function for sending email on team members request to superuser
def SendEmailLeadLimitToSuperUser(data):
    superuser_email = data.get('superuser_email', '')
    member_email = data.get('member_email','')
    superuser_id = data.get('superuser_id','')
    context = {'member_email' : member_email,}

    subject = f'Request: You Got an Request From {member_email}'
    html_message = render_to_string('pages/lead_request_mail.html', context)
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    try:
        return send_mail(subject, plain_message, from_email, [superuser_email], html_message=html_message, fail_silently=False)
    except Exception as e:
        print(f'Email sending failed: {e}')

# helping function - in action
def returnTeamMemberObj(member_eid):
    team_obj = None
    is_uuid_valid = is_valid_uuid(member_eid)
    if is_uuid_valid:
        team_obj = TeamMembers.objects.filter(team_id = member_eid)
    elif '@' in member_eid:
        team_obj = TeamMembers.objects.filter(user__email = member_eid)
    if team_obj:
        return team_obj.first()
    return team_obj


# helping function - in action
def returnSuperuserObj(superuser_eid):
    superuer_obj = None
    is_uuid_valid = is_valid_uuid(superuser_eid)
    if is_uuid_valid:
        superuer_obj = SuperUsers.objects.filter(superuser_id = superuser_eid)
    elif '@' in superuser_eid:
        superuer_obj = SuperUsers.objects.filter(user__email = superuser_eid)
    if superuer_obj:
        return superuer_obj.first()
    return superuer_obj


def CreateUserAccount(name, email, password, account_type):
    user_obj = UserModel.objects.create_user(name=name, email=email, password=password) # type: ignore
    user_obj.account_type = account_type
    user_obj.save()
    return user_obj


def CreateSuperUserAccount(user_obj, company_name, region, llr_apikey, is_ush=True ):
    superuser = SuperUsers(user = user_obj, company_name = company_name, region = region, llr_apikey = llr_apikey)
    if is_ush:
        superuser.ACCOUNT_TYPE = SuperUsers.ACCOUNT_TYPE.USHADVISOR # type: ignore
    superuser.save()


def CreateALLAuthEmailAddress(user_obj, email):
    EmailAddress.objects.create(user=user_obj, email=email, verified = True, primary=True)


def API_GetPhoneTypeData(superuser_obj, phone_clean):
    is_callblock = False 
    linetype = ''
    dnctype = ''
    if superuser_obj.account_type == 'ush':
        is_callblock = USHA().DonotCallAPI(phone_clean)

    # if superuser_obj.llr_apikey:    
    api_keys = []
    api_keys.append(superuser_obj.llr_apikey)

    if len(api_keys) > 0 :
        llr_obj = LandlineRemoverAPI(api_keys)
        llr_result = llr_obj.GetNumberData(phone_clean)
        linetype = llr_result['linetype']
        dnctype = llr_result['dnctype']

    return is_callblock, linetype, dnctype



def API_AssignTask(one_lead_obj, superuser_obj, team_members_qs):
    team_members_qs = team_members_qs.order_by('pk')
    task = one_lead_obj
    #getting member obj who got last task
    lasttask_member_obj = LastTask.objects.filter(superuser=superuser_obj)

    if lasttask_member_obj: 
        lasttask_member_obj = lasttask_member_obj.first() 

    #making teams objects iterable
    teams = cycle(team_members_qs)
    
    if lasttask_member_obj: 
        for i in range(team_members_qs.count()):
            team_member_obj = next(teams)
            if team_member_obj.team_id == lasttask_member_obj.team_member.team_id: # type: ignore
                break
    
    no_of_agents = team_members_qs.count()
    task_state = get_clean_state(task.state)
    task_assigned = False
    team_limits = {}

    for teamlimit in team_members_qs:
        team_limits[str(teamlimit.team_id)] = teamlimit.campaign_data().assign_leads_limit



    for i in range(no_of_agents):
        team_member_obj = next(teams)
        team_id = str(team_member_obj.team_id)
        leads_limit = team_limits.get(team_id, 0)
        all_status_allow = team_member_obj.all_states
        states_list = team_member_obj.states_list

        is_state_match_with_agent = states_list.get(task_state, False)
        if is_state_match_with_agent is not False: is_state_match_with_agent = True

        agent_already_checked = checkAgentLeadAlreadyExist(task.phone, 
                                                            team_member_obj.user, 
                                                            superuser_obj
                                                            )
        if agent_already_checked:
            pass

        elif (leads_limit==-1 or leads_limit>0) and (all_status_allow or is_state_match_with_agent):
            # print("if conidtion triggered")
            LeadsDistribution.objects.create(assign_to = team_member_obj.user, lead = task)
            if leads_limit > 0:
                team_limits[team_id] += -1
            task_assigned = True
            break 

    #update remaining limits of members in campaign table 
    campaign_update_objects = []
    campaign_members_qs = TextDripCampaign.objects.filter(team_member__team_id__in=list(team_limits.keys()))
    for campaign_obj in campaign_members_qs:
        campaign_obj.assign_leads_limit = team_limits.get(str(campaign_obj.team_member.team_id), -1)
        campaign_update_objects.append(campaign_obj)

    if len(campaign_update_objects) > 0:
        TextDripCampaign.objects.bulk_update(campaign_update_objects, ['assign_leads_limit'])


    if lasttask_member_obj: 
        lasttask_member_obj.team_member = team_member_obj # type: ignore
        lasttask_member_obj.save() # type: ignore
    else:
        LastTask.objects.create(team_member=team_member_obj, superuser=superuser_obj)

    #checking user is allow to send TD contact
    userprofile = UserProfile.objects.get(user=superuser_obj.user)
    if userprofile.is_td_contact == True:
        #send to textdrip contact 
        handleTDCREATECONTACT(one_lead_obj, team_member_obj, superuser_obj)
    
    teams = None
    team_members_qs = None
    return task_assigned


#supportive function
def returnContactDataFromOBJ(lead_obj):
    lead_data = model_to_dict(lead_obj)
    keys_to_remove = ['id', 'superuser', 'lead_file', 'linetype', 'dnctype', 'is_callblock', 'is_ready', 'is_assigned']
    def remove_keys(key):
        try: lead_data.pop(key, None)
        except: pass  
    list(map(remove_keys, keys_to_remove))
    return lead_data

def handleTDCREATECONTACT(lead_obj, team_member_obj, superuser_obj):
    try:
        #send to textdrip contact 
        campaign_member_obj = TextDripCampaign.objects.get(team_member=team_member_obj, superuser=superuser_obj)
        lead_data = returnContactDataFromOBJ(lead_obj)
        lead_data['tags'] = [{"value": item} for item in lead_data['tags'].split(',')]
        textdrip_obj.CreateContact(
            auth_token=campaign_member_obj.textdrip_apikey,
            campaign_id=campaign_member_obj.textdrip_compaign_id,
            data=lead_data,
            is_usha=superuser_obj.is_usha_account
        )
    except: pass
    return None


def handle_td_contact_bulk(leadfile_uid):
    lead_file_obj = LeadsFile.objects.get(uid=leadfile_uid)
    leadsfiledata_qs = lead_file_obj.return_total_assigned_leads()
    superuser_obj  = lead_file_obj.get_superuser_obj()
    # check is user allowed to send td contact 
    userprofile = UserProfile.objects.get(user=superuser_obj.user)
    if userprofile.is_td_contact == False:
        #print("yes we are not sending any contacts for ", userprofile)
        return None
    for task in leadsfiledata_qs[:]:
        get_lead_agent = task.get_lead_agent().get_member_obj() # type: ignore
        td_campaign_data = TextDripCampaign.objects.filter(team_member=get_lead_agent, superuser=superuser_obj).values('textdrip_apikey', 'textdrip_compaign_id')
        try:
            lead_data = returnContactDataFromOBJ(task)
            lead_data['tags'] = [{"value": item} for item in lead_data['tags'].split(',')]
            textdrip_obj.CreateContact(
                auth_token=td_campaign_data[0]['textdrip_apikey'],
                campaign_id=td_campaign_data[0]['textdrip_compaign_id'],
                data=lead_data,
                is_usha=superuser_obj.is_usha_account
            )
        except:pass
    return None


def is_llr_apikey_valid(apikey):
    try:
        llr_obj = LandlineRemoverAPI()
        GetAPIStatus = llr_obj.GetAPIStatus(apikey)
        remaining_credits = GetAPIStatus['data']['RemainingCredits']
        return True  # type: ignore
    except:
        return False


def getLLRCredits(apikey):
    llr_obj = LandlineRemoverAPI()
    GetAPIStatus = llr_obj.GetAPIStatus(apikey)
    try:
        return GetAPIStatus['data']['RemainingCredits']  # type: ignore
    except:
        return 0


#use for home page > dashboard.views.HomeView
#use for htmx on create lead page. 
def getLLRAPIStatus(apikey):
    llr_obj = LandlineRemoverAPI()
    GetAPIStatus = llr_obj.GetAPIStatus(apikey)
    try:
        remaining_credits = GetAPIStatus['data']['RemainingCredits']
        is_topup_on = GetAPIStatus['data']['IsAutoTopUpOn']
        return remaining_credits, is_topup_on
    except:
        return None, None

def checkTeamMemberCampaign(leadfile_uid):
    lead_file_obj = LeadsFile.objects.get(uid=leadfile_uid)
    leadsfiledata_qs = lead_file_obj.return_total_assigned_leads()  # return_leadsfiledata_qs()
    superuser_obj = lead_file_obj.get_superuser_obj()

    active_team_list = lead_file_obj.return_team_ids_list()
    team_members_qs = superuser_obj.teams.all().filter(team_id__in=active_team_list,
                                                       textdripcampaign__is_campaign_activated=True).order_by(
        'pk').order_by('pk').values('team_id', 'textdripcampaign__textdrip_apikey',
                                    'textdripcampaign__textdrip_compaign_id', 'user__email')

    team_members_qs_full = superuser_obj.teams.all().filter(team_id__in=active_team_list).order_by('pk').order_by('pk')

    active_campaign_team_member_list = []
    deactive_campaign_team_member_list = []
    for team_member_data in team_members_qs:
        textdrip_apikey = team_member_data['textdripcampaign__textdrip_apikey']
        textdrip_compaign_id = team_member_data['textdripcampaign__textdrip_compaign_id']

        td_obj = TextDrip()
        campaign_data_response = td_obj.GetCampaignDripMessage(auth_token=textdrip_apikey,
                                                               campaign_id=textdrip_compaign_id)

        # Check if campaign_data is True (boolean value)
        if campaign_data_response is True:
            active_campaign_team_member_list.append(
                team_members_qs_full.get(team_id=team_member_data['team_id']))  # Append the TeamMembers instance
        elif campaign_data_response is False:
            team_member = team_members_qs_full.get(team_id=team_member_data['team_id'])
            campaign_obj = TextDripCampaign.objects.get(team_member=team_member, superuser=superuser_obj)
            campaign_obj.is_campaign_activated = False
            campaign_obj.assign_leads_limit = 0
            campaign_obj.save()
            deactive_campaign_team_member_list.append(team_member)

    if deactive_campaign_team_member_list:
        InvalidCampaignAlertSuperUserSendEmail(superuser_obj, [team_member.user.email for team_member in
                                                               deactive_campaign_team_member_list])

        for team_member in deactive_campaign_team_member_list:
            data = {
                'superuser_id': superuser_obj.superuser_id,
                'member_id': team_member.team_id,
                'redirect_url': settings.SITE_DOMAIN_LINK.split('//')[1]
            }

            InvalidCampaignAlertTeamMemberSendEmail(superuser_obj,team_member.user.email,data)