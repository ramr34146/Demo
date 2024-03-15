#django imports
from django.db.models import Sum
from time import sleep
from django.shortcuts import redirect, render
from django.views.generic import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import  HttpResponse
from django.db.models import Q
from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse, FileResponse, Http404
from django.contrib.auth import get_user_model
UserModel = get_user_model()
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views.generic import View, ListView, DetailView
#other imports


#custom imports

from dashboard.models import LeadsFile, LeadsDistribution, LeadsFileData, Activity, Tag
from users.models import TeamMembers, SuperUsers, UserProfile, TextDripCampaign, LeadsLimitRequest
from utils.log import(
    create_log_activity,
    update_log_activity,
    delete_log_activity
    )

class DummyFile:
    def write(self, value_to_write):
        return value_to_write


from utils.utils import *
from utils.celery_tasks_utils import terminateTask

from utils.handle_django import (
        SendInvitationEmailToMember,
        returnSuperuserObj, 
        returnTeamMemberObj,
        CreateUserAccount,
        getLLRCredits,
        getLLRAPIStatus,
        SendEmailLeadLimitToSuperUser,
    )

from utils.celery_tasks import HandleLeadsDataWithAssigned


class HomeView(LoginRequiredMixin, View):
    template_name = "dashboard/home.html"
    def get(self, request, *args, **kwargs):
        current_user = request.user 
        if current_user.account_type == 'sup':
            superuser = SuperUsers.objects.get(user=current_user)
            context = {
                'is_superuser' : True,
                'superuser' : superuser
            }

            if len(str(superuser.llr_apikey).strip()) == 40: 
                remaining_credits, is_topup_on  = getLLRAPIStatus(superuser.llr_apikey)
                if remaining_credits:
                    context['llr_credits'] = remaining_credits #f"{getLLRCredits(superuser.llr_apikey):,}"
                    context['llr_auto_topup'] = is_topup_on
            try:
                total_uploaded_leads = LeadsFile.objects.filter(user=current_user).aggregate(Sum('total_leads'))
                context['total_uploaded_leads'] = f"{total_uploaded_leads['total_leads__sum']:,}"
            except:
                context['total_uploaded_leads'] = 0
                
            context['api_leads'] = LeadsFileData.objects.filter(superuser=superuser, lead_file=None).count()

        elif current_user.account_type == 'team':
            context = {
                'is_teammeber' : True,
                'team_member' : TeamMembers.objects.get(user=current_user)
            }
        else:
            return redirect('core:home')

        context['user'] = current_user
        context['profile'] = UserProfile.objects.get(user=current_user)
        
        return render(request, self.template_name, context)

 
class APIView(LoginRequiredMixin, View):
    template_name = "dashboard/api_home.html"
    def get(self, request, *args, **kwargs):
        current_user = request.user 
        if current_user.account_type == 'sup':
            context = {
                'superuser' : SuperUsers.objects.get(user=current_user),
                'profile' : UserProfile.objects.get(user=current_user)
            }
        else:
            return redirect('core:home')
        return render(request, self.template_name, context)


class AllLeadListView(LoginRequiredMixin, ListView): 
    template_name= "dashboard/leads_list.html"
    context_object_name = 'projects'  
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_queryset(self):
        current_user = self.request.user
        if current_user.account_type == 'sup':
            return LeadsFile.objects.filter(user=current_user).exclude(status=LeadsFile.FILE_STATUS.STARTED)
        else:
            messages.info(self.request, 'You are not allowed to view that page.')
            return redirect('core:home')

        
class AllAPILeadListView(LoginRequiredMixin, View): 
    template_name_super = "dashboard/api_leads_list.html"

    def get(self, request, *args, **kwargs):
        current_user = request.user
        if current_user.account_type == 'sup':
            api_leads = LeadsFileData.objects.filter(superuser__user=current_user, lead_file=None)
            context = {
                'api_leads':api_leads,
            }
            return render(request, self.template_name_super, context)
        else:
            messages.info(request, 'You are not allowed. Contact Support')
        return redirect('core:home')
 

class LeadDetails(LoginRequiredMixin, ListView):
    template_name = "dashboard/leads_detail.html"
    context_object_name = 'leads'  
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        leadfile_uid=self.kwargs['UID']
        context['project'] =  LeadsFile.objects.get(user=self.request.user, uid=leadfile_uid)
        return context

    def get_queryset(self):
        leadfile_uid=self.kwargs['UID']
        return LeadsFile.objects.get(user=self.request.user, uid=leadfile_uid).return_leadsfiledata_qs()


class CreateLeadView(LoginRequiredMixin, View):
    template_name = "dashboard/leads_create.html"
    
    def get(self, request, *args, **kwargs):
        current_user = request.user
        if current_user.account_type == 'sup':
            teams = SuperUsers.objects.get(user=current_user).teams.all()
            if teams.count() == 0:
                messages.info(request, 'You Should have a at least 1 team member to upload a Lead')
                return redirect('auth:home')

            vacation_mode_list = list(teams.exclude(vacation_mode=False).values_list('team_id', flat=True))
            vacation_mode_list = [_ for _ in vacation_mode_list]
            disable_member = TextDripCampaign.objects.exclude(team_member__team_id__in=vacation_mode_list).filter(superuser__user=current_user).filter(is_temporary_disabled=True).count()
            vacation_mode = len(vacation_mode_list)

            context = {
                'total_members': teams.count(),
                'vacation_mode': vacation_mode,
                'disable_members': disable_member,
                'active_members': teams.count() - vacation_mode - disable_member,
            }
            
            return render(request, self.template_name, context)
        else:
            return redirect('auth:home')

    def post(self, request,*args, **kwargs):
        if request.FILES['csv_file_upload']:
            try:
                current_user = self.request.user
                # return render(request, self.template_name, {})
                project_name = str(self.request.POST.get('project_name')).strip()
                project_description = str(self.request.POST.get('project_description')).strip()
                project_csv_file = request.FILES["csv_file_upload"]
                tag_name = request.POST.get("tag_name", None)

                if request.POST.get("dnc_check", None) is not None: 
                    dnc_check = True
                else:
                    dnc_check = False

                if request.POST.get("do_not_distribute", None) is not None: 
                    do_not_distribute = True
                else:
                    do_not_distribute = False

                if request.POST.get("allow_llr_site", None) is not None: 
                    allow_llr_site = True
                else:
                    allow_llr_site = False

                # print(dnc_check, do_not_distribute)
                # return redirect(reverse('auth:leads_create'))

                if not project_csv_file.name.endswith('.csv'):
                    messages.info(request, 'Please upload .CSV File')
                    return redirect(reverse('auth:leads_create'))


                leadfile_obj = LeadsFile.objects.create(user = current_user, 
                                                    csvfile = project_csv_file, 
                                                    project_name = project_name,
                                                    project_description = project_description,
                                                    csvfile_name = project_csv_file.name,
                                                    is_dnc_block = dnc_check,
                                                    is_distribution_block = do_not_distribute,
                                                    is_llr_allow = allow_llr_site,
                                                    tags=tag_name.strip()
                                                    )

                totalrows, headers = HandleLeadCsvFile(leadfile_obj.csvfile.path)
                leadfile_obj.total_leads = totalrows
                super_user_obj = SuperUsers.objects.get(user=current_user)
                # leadfile_obj.team_ids = [str(uid['team_id']) for uid in super_user_obj.teams.exclude(vacation_mode=True).values('team_id')]
                team_ids = [str(uid['team_id']) for uid in super_user_obj.teams.exclude(vacation_mode=True).values('team_id')]
                disable_ids = [str(uid['team_member__team_id']) for uid in  TextDripCampaign.objects.filter(team_member__team_id__in=team_ids, 
                                                    superuser=super_user_obj).filter(is_temporary_disabled=True).values('team_member__team_id')]
                

                update_team_ids =  list(set(team_ids) - set(disable_ids))
                leadfile_obj.team_ids = update_team_ids
                leadfile_obj.save()

                create_log_activity(current_user,"Create project successfully")

                campaign_obj_enable_ids = ()
                if campaign_obj_enable_ids:
                    campaign_obj_enable_ids = campaign_obj_enable_ids[0]['team_member__team_id']

                """
                    ['0fc1b47b-7906-4d0d-a093-b12c893c81f8', 'a3cc5530-0a16-489f-92e3-953211eeb9ba', 'b5e760ac-9def-471f-824a-074b962d315e', 'bd6a3d3a-d4b6-4d20-a9a8-d26816ded0d2']
                    result we want:  ['a3cc5530-0a16-489f-92e3-953211eeb9ba', 'b5e760ac-9def-471f-824a-074b962d315e']
                """

                context = {
                    "totalrows" : totalrows,
                    "headers" : headers,
                    "csvfile": leadfile_obj,
                } 

                # check LLR credit less than total records
                try:
                    llr_apikey = super_user_obj.llr_apikey
                    if llr_apikey:
                        remaining_credits, is_topup_on = getLLRAPIStatus(llr_apikey)
                        if remaining_credits < totalrows:
                            context['less_credit'] = True
                except :
                    context['LLR_keyInvalid'] = True
                    pass

                # For Sweet Alert of the Leads limit is less than the totalrows
                textdripCampaign_obj = TextDripCampaign.objects.filter(superuser=super_user_obj)
                if TextDripCampaign.objects.filter(superuser=SuperUsers.objects.get(user=current_user), assign_leads_limit=-1).count() == 0:
                    total_assign_leads_limit = textdripCampaign_obj.aggregate(total_assign_leads_limit=Sum('assign_leads_limit')).get('total_assign_leads_limit', 0)
                    if totalrows > total_assign_leads_limit:
                        context['total_assign_leads_limit'] = True

                return render(request, "dashboard/select_headers.html", context)
            except:
                messages.info(request, "Failed To Upload. Please check your csv file and try again.")

        return redirect(reverse('auth:leads_create'))


class SelectHeadersView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):  
        return redirect(reverse('auth:leads_create'))

    def post(self, request, *args, **kwargs): 
        if request.method =='POST':
            current_user = request.user 
            leadfile_uid = self.request.POST.get('header_uuid')
            header_firstname = str(self.request.POST.get('header_firstname')).strip()
            header_lastname = str(self.request.POST.get('header_lastname')).strip()

            header_phonenumber = str(self.request.POST.get('header_phonenumber')).strip()

            if not all([header_firstname, header_phonenumber]):
                messages.info(request, "Failed To Upload. Please Choose Name and Phone Column Properly.")
                return redirect(reverse('auth:leads_create'))

            header_email = str(self.request.POST.get('header_email')).strip()
            header_birthdate = str(self.request.POST.get('header_birthdate')).strip()
            header_address = str(self.request.POST.get('header_address')).strip()
            header_state = str(self.request.POST.get('header_state')).strip()
            header_zipcode = str(self.request.POST.get('header_zipcode')).strip()
            header_custom_field1 = str(self.request.POST.get('header_custom_field1')).strip()
            header_custom_field2 = str(self.request.POST.get('header_custom_field2')).strip()
            header_custom_field3 = str(self.request.POST.get('header_custom_field3')).strip()
            header_custom_field4 = str(self.request.POST.get('header_custom_field4')).strip()
            header_custom_field5 = str(self.request.POST.get('header_custom_field5')).strip()

            #save data into model
            leadfile_obj = LeadsFile.objects.get(user=current_user, uid=leadfile_uid)


            #modified version - read csv file and upload into LeadsFiledata
            superuser_obj = SuperUsers.objects.get(user=current_user)
            batch_size = 1000 # set the batch size here
            clean_data = pd.read_csv(leadfile_obj.csvfile.path, encoding='latin-1', 
                            low_memory=True, on_bad_lines='skip', 
                            skip_blank_lines=True, skipinitialspace=True, 
                            dtype=str, chunksize=batch_size)
            
            # clean_data.dropna(how="all", inplace=True)
            for i, chunk_data in enumerate(clean_data):
                # if i != 0 : continue
                # print(chunk_data.shape[0])
                chunk_data.dropna(how="all", inplace=True)
                chunk_data[header_phonenumber] = chunk_data[header_phonenumber].apply(returnCleanPhone)
                chunk_data = chunk_data.to_dict(orient='records')

                leadsfiledata_objs = []
                for data in chunk_data:
                    clean_phone_number = data.get(header_phonenumber, None) #returnCleanPhone(data.get(header_phonenumber, None))
                    if not clean_phone_number: continue 

                    if header_lastname:
                        full_name = str(data.get(header_firstname, '')) + " " + str(data.get(header_lastname, ''))
                    else:
                        full_name = str(data.get(header_firstname, ''))



                    clean_phone_number = returnCleanPhone(data.get(header_phonenumber, None))

                    leadsfiledata_objs.append(
                        LeadsFileData(superuser = superuser_obj,
                            lead_file = leadfile_obj, 
                            name = full_name,
                            phone = clean_phone_number,
                            email = data.get(header_email, ''),
                            birthdate = data.get(header_birthdate, ''),
                            address = data.get(header_address, ''),
                            state = data.get(header_state, ''),
                            zipcode = data.get(header_zipcode, ''),
                            custom_field1 = data.get(header_custom_field1, ''),
                            custom_field2 = data.get(header_custom_field2, ''),
                            custom_field3 = data.get(header_custom_field3, ''),
                            custom_field4 = data.get(header_custom_field4, ''),
                            custom_field5 = data.get(header_custom_field5, ''),
                            tags=leadfile_obj.tags,
                        )
                    )

                if len(leadsfiledata_objs) > 0:
                    LeadsFileData.objects.bulk_create(leadsfiledata_objs, ignore_conflicts=True, batch_size=500)
                leadsfiledata_objs = None #clear memory
            clean_data = None #clear memory

            taskid = HandleLeadsDataWithAssigned.delay(leadfile_uid)
            leadfile_obj.taskid = taskid.id
            leadfile_obj.status = LeadsFile.FILE_STATUS.PROCESSED 
            leadfile_obj.save()

            create_log_activity(current_user,"File has been Added & Tasks will be Distributed in Your Team Members.")
            messages.info(request, "File has been Added & Tasks will be Distributed in Your Team Members.")
            return redirect(reverse('auth:leads_list'))


class CancelLeadView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):  
        return redirect(reverse('auth:leads_create'))

    def post(self, request, *args, **kwargs): 
        if request.method =='POST':
            current_user = request.user 
            project_task_id = self.request.POST.get('project_task_id')
            lead_file_obj = LeadsFile.objects.get(user=current_user, taskid=project_task_id)
            
            terminateTask(project_task_id)

            lead_file_obj.status = LeadsFile.FILE_STATUS.CANCELLED
            lead_file_obj.save()
            delete_log_activity(current_user,"Project has been terminated successfully")
            messages.info(request, "Project has been terminated.")
            return redirect(reverse('auth:leads_list'))


class TeamList(LoginRequiredMixin, View):
    template_name = "dashboard/members_list.html"
    def get(self, request, *args, **kwargs): 
        current_user = request.user
        superuser = SuperUsers.objects.get(user=current_user)
        team_members = superuser.teams.all().order_by('-pk')
        for tm in team_members:
            tm.campaign_data_extend = TextDripCampaign.objects.filter(team_member=tm, superuser=superuser).first()

        context = {
            'team_members': team_members,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        current_user = request.user
        member_eid = str(self.request.POST.get('member_id', '')).strip()
        team_obj = returnTeamMemberObj(member_eid)

        if 'leadlimit' in request.POST:
            superuser = SuperUsers.objects.get(user=current_user)
            team_members = superuser.teams.all().order_by('-pk')
            leadlimit=request.POST.get('leadlimit')
            for tm in team_members:
                tm.campaign_data_extend = TextDripCampaign.objects.filter(team_member=tm, superuser=superuser,assign_leads_limit=leadlimit).first()
            context = {
                'team_members': team_members,
            }
            return render(request, "dashboard/members_list_filter.html", context)


        if 'update_leads_limit' in request.POST:
            update_leads_limit = int(self.request.POST.get('update_leads_limit', -1))
            TextDripCampaign.objects.filter(team_member=team_obj, superuser=SuperUsers.objects.get(user=current_user)).update(assign_leads_limit=update_leads_limit)
            update_log_activity(current_user,'Assign leads limit has been updated successfully!')
            messages.info(request, f"Assign leads limit has been updated successfully!")
        else:
            data = {
                'superuser_name' : current_user.name.title() ,
                'superuser_id' : current_user.superusers.superuser_id,
                'member_email' : team_obj.user.email,
                'member_id' : team_obj.team_id,
                'redirect_url': settings.SITE_DOMAIN_LINK.split('//')[1]
            }
            try:
                TextDripCampaign.objects.filter(team_member=team_obj, superuser=SuperUsers.objects.get(user=current_user)).update(is_campaign_activated=False)
                SendInvitationEmailToMember(data)
                update_log_activity(current_user,'Update Campaign Email has been send')
                messages.info(request, f"Update Campaign Email has been sent to {team_obj.user.email}")
            except:
                messages.info(request, f"Failed to send Update Campaign Email to {team_obj.user.email}")
        return redirect('auth:team_list')

class TeamList_LeadsLimit(LoginRequiredMixin, View):
    template_name = "dashboard/members_list_limit_zero.html"
    def get(self, request, *args, **kwargs):
        current_user = request.user
        superuser = SuperUsers.objects.get(user=current_user)
        team_members = superuser.teams.all().order_by('-pk')
        for tm in team_members:
            tm.campaign_data_extend = TextDripCampaign.objects.filter(team_member=tm, superuser=superuser, assign_leads_limit=0).first()

        context = {
            'team_members': team_members,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        current_user = request.user
        member_eid = str(self.request.POST.get('member_id', '')).strip()
        team_obj = returnTeamMemberObj(member_eid)

        if 'update_leads_limit' in request.POST:
            update_leads_limit = int(self.request.POST.get('update_leads_limit', -1))
            TextDripCampaign.objects.filter(team_member=team_obj, superuser=SuperUsers.objects.get(user=current_user)).update(assign_leads_limit=update_leads_limit)
            update_log_activity(current_user,"Assign leads limit has been updated successfully")
            messages.info(request, f"Assign leads limit has been updated successfully!")

        else:
            data = {
                'superuser_name' : current_user.name.title() ,
                'superuser_id' : current_user.superusers.superuser_id,
                'member_email' : team_obj.user.email,
                'member_id' : team_obj.team_id,
            }
            try:
                TextDripCampaign.objects.filter(team_member=team_obj, superuser=SuperUsers.objects.get(user=current_user)).update(is_campaign_activated=False)
                SendInvitationEmailToMember(data)
                update_log_activity(current_user,"Update Campaign Email has been send")

                messages.info(request, f"Update Campaign Email has been sent to {team_obj.user.email}")
            except:
                messages.info(request, f"Failed to send Update Campaign Email to {team_obj.user.email}")
        return redirect('auth:team_list')

class MasterReset_LeadsLimit_By_SuperUser(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        current_user = request.user
        if 'master_reset_leads_limit' in request.POST:
            if TextDripCampaign.objects.filter(superuser=SuperUsers.objects.get(user=current_user), assign_leads_limit=0).count()==0:
                messages.info(request, f"Team Members with 0 Limit No Record Found")
                return redirect('auth:team_list_leads_limit')

            master_reset_leads_limit = int(self.request.POST.get('master_reset_leads_limit', -1))
            TextDripCampaign.objects.filter(superuser=SuperUsers.objects.get(user=current_user), assign_leads_limit=0).update(assign_leads_limit=master_reset_leads_limit)
            update_log_activity(current_user,'All the Team members leads limit has been updated successfully!')
            messages.info(request, f"All the Team members leads limit has been updated successfully!")
            return redirect('auth:team_list')

class LinkTeamMember(LoginRequiredMixin, View):
    template_name = "dashboard/members_link.html"
    def get(self, request, *args, **kwargs): 
       return render(request, self.template_name, {})
    
    def post(self, request,*args, **kwargs):
        current_user = request.user
        if current_user.account_type != 'sup': return redirect('core:home')
        member_eid = str(self.request.POST.get('member_eid', '')).strip()
        team_obj = returnTeamMemberObj(member_eid)

        create_log_activity(current_user,"Team Member Invitation Email has been sent successfully")

        if team_obj:
            if team_obj in SuperUsers.objects.get(user=current_user).teams.all():
                messages.info(request, f"{member_eid} is already part of your team.")
                return redirect('auth:link_team_member')
            else:
                data = {
                    'superuser_name' : current_user.name.title() ,
                    'superuser_id' : current_user.superusers.superuser_id,
                    'member_email' : team_obj.user.email,
                    'member_id' : team_obj.team_id,
                    'redirect_url': settings.SITE_DOMAIN_LINK.split('//')[1]
                }
                SendInvitationEmailToMember(data)
                messages.info(request, f"Invitation Email has been sent to {team_obj.user.email}")
                return redirect('auth:link_team_member')
        else:
            if isValidEmailFormat(member_eid):
                #check if email is a superuser account
                superuser_obj = returnSuperuserObj(member_eid)
                if superuser_obj:
                    team_obj = TeamMembers.objects.create(user = superuser_obj.user)
                else:
                    user_obj = CreateUserAccount(name=str(member_eid).split('@')[0], email=member_eid, password=generatePassword(), account_type='team')
                    team_obj = TeamMembers.objects.create(user = user_obj)

                data = {
                    'superuser_name' : current_user.name.title() ,
                    'superuser_id' : current_user.superusers.superuser_id,
                    'member_email' : team_obj.user.email,
                    'member_id' : team_obj.team_id,
                    'redirect_url': settings.SITE_DOMAIN_LINK.split('//')[1]
                }
                SendInvitationEmailToMember(data)
                messages.info(request, f"Invitation Email has been sent to {team_obj.user.email}")
                return redirect('auth:link_team_member')
            else:
                messages.info(request, "Email is not Valid! Please Try another Valid Email address")
                return redirect('auth:link_team_member')

        messages.info(request, "Something went wrong. Please Contact Support")
        return redirect('auth:link_team_member')


class UnlinkTeamMember(LoginRequiredMixin, View):
    template_name = "dashboard/members_unlink.html"
    def get(self, request, *args, **kwargs): 
       return render(request, self.template_name, {})
    
    def post(self, request,*args, **kwargs):
        if request.method == 'POST':
            current_user = request.user
            member_eid = str(self.request.POST.get('unlink_member', '')).strip()

            team_obj = returnTeamMemberObj(member_eid)
            if team_obj:
                superuser_obj = SuperUsers.objects.get(user=current_user)
                superuser_obj.teams.remove(team_obj)
                superuser_obj.save()
                delete_log_activity(current_user,"Team Member has been Unlinked Successfully")

                try:
                    TextDripCampaign.objects.filter(team_member=team_obj, superuser=superuser_obj).update(is_campaign_activated=False)
                except:
                    pass

                messages.info(request, "Team Member has been Unlinked Successfully")
                return redirect('auth:team_list')

            messages.info(request, "Member is not found! Please Try another Email address or Member ID")
            return redirect('auth:team_list')


# todo: modify it further later 
class DisableEnableTeamMember(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs): 
       return render(request, self.template_name, {})
    
    def post(self, request,*args, **kwargs):
        current_user = request.user
        if current_user.account_type == 'sup':
            member_eid = str(self.request.POST.get('team_member_id', '')).strip()
            team_obj = returnTeamMemberObj(member_eid)
            if team_obj:
                if team_obj.vacation_mode:
                    messages.info(request, "Team Member has turned on the vacation mode. All future leads will be skipped for this member.")
                superuser_obj = SuperUsers.objects.get(user=current_user)
                textdripcampaign_obj = TextDripCampaign.objects.filter(team_member=team_obj, superuser=superuser_obj).first()
                if textdripcampaign_obj.is_temporary_disabled:
                    #enable it 
                    textdripcampaign_obj.is_temporary_disabled = False 
                    update_log_activity(current_user,"Team Member has been enabled successfully")
                    messages.info(request, "Team Member has been enabled Successfully")
                else:
                    #disbale it 
                    textdripcampaign_obj.is_temporary_disabled = True
                    update_log_activity(current_user,"Team Member has been disabled successfully")
                    messages.info(request, "Team Member has been disabled Successfully")
                textdripcampaign_obj.save()

                return redirect('auth:team_list')

            messages.info(request, "Member is not found! Please Try another Email address or Member ID")
            return redirect('auth:team_list')

        elif current_user.account_type == 'team':
            superuser_id = str(self.request.POST.get('superuser_id', '')).strip()
            team_obj = TeamMembers.objects.get(user=current_user)
            superuser_obj = returnSuperuserObj(superuser_id)
            
            textdripcampaign_obj = TextDripCampaign.objects.filter(team_member=team_obj, superuser=superuser_obj).first()
            if textdripcampaign_obj.is_temporary_disabled:
                #enable it 
                textdripcampaign_obj.is_temporary_disabled = False 
                update_log_activity(current_user,"Superuser has been enabled Successfully")
                messages.info(request, "Superuser has been enabled Successfully")
            else:
                #disbale it 
                textdripcampaign_obj.is_temporary_disabled = True
                update_log_activity(current_user,"Superuser has been disabled Successfully")

                messages.info(request, "Superuser has been disabled Successfully")
            textdripcampaign_obj.save()
            return redirect('auth:member_superuser_list')

        else:
            return redirect('core:home')

class UpdateLeadsLimitView(LoginRequiredMixin, View):
    def post(self, request):
        selected_checkbox_values = request.POST.getlist('selected_checkboxes')

        if not selected_checkbox_values or selected_checkbox_values[0] == '':
            messages.error(request, 'No team members selected. Please select at least one team member.')
            return redirect('auth:team_list')

        selected_team_member_ids = selected_checkbox_values[0].split(',')
        new_leads_limit = request.POST.get('update_leads_limit')
        try:
            for team_member_id in selected_team_member_ids:
                team_member = TeamMembers.objects.get(team_id=team_member_id)
                campaign = team_member.campaign_data()
                if campaign:
                    campaign.assign_leads_limit = new_leads_limit
                    campaign.save()
            update_log_activity(request.user,'All Team Member Leads limit updated successfully!')
            messages.success(request, 'Leads limit updated successfully!')
            return redirect('auth:team_list')
        except TeamMembers.DoesNotExist:
            messages.error(request, 'Team member not found.')
        return redirect('auth:team_list')

class TeamDetailView(LoginRequiredMixin, ListView):
    template_name = "dashboard/members_detail.html"

    context_object_name = 'leads'  
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member_id = self.kwargs['UID']
        member_obj = returnTeamMemberObj(member_id)
        context['total_leads'] = self.get_queryset().count()
        context['member'] =  member_obj
        return context

    def get_queryset(self):
        current_user = self.request.user
        member_id = self.kwargs['UID']
        member_obj = returnTeamMemberObj(member_id)
        superuser_obj = SuperUsers.objects.get(user=current_user)
        leads_data = LeadsDistribution.objects.filter(assign_to=member_obj.user, lead__superuser=superuser_obj)
        return leads_data


class LeadFileDownloadView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            leadfile_uid = kwargs['UID']
            current_user = request.user
            leadsfile_obj = LeadsFile.objects.get(uid=leadfile_uid) #user=current_user, 
            if request.user.is_superuser == False and current_user != leadsfile_obj.user:
                messages.info(request, 'You are not allowed to download this file.')
                return redirect('auth:home')

            rows = []
            download_filter = request.GET.get('filter') or None
            
            if download_filter == 'assigned':
                leads_data = leadsfile_obj.return_total_assigned_leads()
            elif download_filter == 'skipped':
                leads_data = leadsfile_obj.return_total_leads_skipped()
            elif download_filter == 'callblocked':
                leads_data = leadsfile_obj.return_total_leads_callblock()
            elif download_filter == 'litigator':
                leads_data = leadsfile_obj.return_total_leads_litigator()
            elif download_filter == 'dnc':
                leads_data = leadsfile_obj.return_total_leads_dnctype()
            elif download_filter == 'clean':
                leads_data = leadsfile_obj.return_total_leads_clean()
            else:
                leads_data = leadsfile_obj.return_leadsfiledata_qs()

            if download_filter:
                filename = f"{leadfile_uid}_{download_filter}.csv"
            else:
                filename = f"{leadfile_uid}_full.csv"

            # Csv File output: Modify the output methods and add the user uploaded extra file columns into the final/filtered output file.

            # for i, lead in enumerate(leads_data):
            #     rows.append([
            #         i+1, lead.name, lead.phone, lead.email, lead.get_lead_agent_display(), lead.is_callblock, lead.linetype, lead.dnctype, lead.updated_at
            #     ])
            # rows.insert(0, ['Sr.', 'Name', 'Phone', 'Email', 'Assigned To', 'Call Block', 'Line Type', 'Dnc Type', 'Added At'])

            rows = extra_file_columns_filter_output(leads_data)

            writer = csv.writer(DummyFile(), delimiter=',')
            data = [writer.writerow(row) for row in rows]
            response = StreamingHttpResponse(data, content_type="text/csv")
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except:
            messages.info(request, 'You are not allowed to download this file.')
            return redirect('auth:home')


#for member account
class MemberLeadListView(LoginRequiredMixin, ListView): 
    template_name= "dashboard/members/leads_list_team.html"

    context_object_name = 'leads'  
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_leads'] = self.get_queryset().count()
        return context

    def get_queryset(self):
        current_user = self.request.user
        if current_user.account_type == 'team':
            return LeadsDistribution.objects.filter(assign_to=current_user)
        else:
            messages.info(self.request, 'You are not allowed to view that page.')
            return redirect('core:home')


#for member account
class AllSuperusersList(LoginRequiredMixin, ListView): 
    template_name= "dashboard/members/superusers_list.html"

    context_object_name = 'objects'  
    paginate_by = 1000


    def get_queryset(self):
        current_user = self.request.user
        if current_user.account_type == 'team':
            superusers = SuperUsers.objects.filter(teams__user=current_user).values_list('user', flat=True)
            td_campaigns = TextDripCampaign.objects.filter(team_member__user=current_user, superuser__user__in=superusers)
            return td_campaigns
        else:
            messages.info(self.request, 'You are not allowed to view that page.')
            return redirect('core:home')


    def post(self, request, *args, **kwargs):
        try:
            current_user = request.user
            team_obj = returnTeamMemberObj(current_user.email)
            superuser_id = str(self.request.POST.get('superuser_id', '')).strip()
            superuser_obj = returnSuperuserObj(superuser_id)
            update_leads_limit = int(self.request.POST.get('update_leads_limit', -1))

            if superuser_obj.assign_leads_limit == -1 or update_leads_limit < 0:
                if update_leads_limit < 0:
                    update_leads_limit = superuser_obj.assign_leads_limit
            elif update_leads_limit > superuser_obj.assign_leads_limit:
                update_leads_limit = superuser_obj.assign_leads_limit

            TextDripCampaign.objects.filter(team_member=team_obj, superuser=superuser_obj).update(assign_leads_limit=update_leads_limit)
            update_log_activity(current_user,"Assign leads limit has been updated successfully")
            messages.info(request, f"Assign leads limit has been updated successfully!")
            return redirect('auth:member_superuser_list')
        except:
            return redirect('auth:member_superuser_list')

class SendEmailLeadLimitView(View):
    def post(self, request, *args, **kwargs):
        try:
            superuser_id = str(self.request.POST.get('superuser_id', '')).strip()
            current_leads_limit = str(self.request.POST.get('current_limit', '')).strip()
            superuser_obj = returnSuperuserObj(superuser_id)
            current_user = request.user
            data = {
                'superuser_email' : superuser_obj,
                'superuser_id' : superuser_id,
                'member_email' : current_user,
            }
            emailsent = SendEmailLeadLimitToSuperUser(data)
            leads_limit_obj = LeadsLimitRequest.objects.create(superuser=superuser_obj,team_member=current_user, current_limit=current_leads_limit)
            create_log_activity(current_user, "Request Leads Limit send to super user")
            messages.info(request, f"Email sent successful for leads limit to super user {superuser_obj}!")
            return redirect('auth:member_superuser_list')
        except:
            messages.info(request, f"Something went wrong! Please try again.")
            return redirect('auth:member_superuser_list')

class HTMX_CHECK_LLR_APIKEY(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs): 
        try:
            invalid_apikey_msg = 'Invalid APIkey <a href="https://leaddistro.textdrip.com/edit-profile/">Update here (if you want to check number\'s LineType & DNCType From LandlineRemover.com) </a>'
            current_user = request.user
            llr_apikey = SuperUsers.objects.values('llr_apikey').get(user=current_user)['llr_apikey']
            if llr_apikey is None:
                msg = invalid_apikey_msg
            else:
                llr_apikey = llr_apikey
                remaining_credits, is_topup_on  = getLLRAPIStatus(llr_apikey)
                if remaining_credits is None:
                    msg = invalid_apikey_msg
                else:
                    if is_topup_on:
                        top_up_icon = '<span class="badge badge-circle badge-success"><i class="bi bi-check-lg text-white"></i></span>'
                    else:
                        top_up_icon = '<span class="badge badge-circle badge-danger"><i class="bi bi-x-lg text-black"></i></span>'
                    msg = f"<span class='text-success'>Valid</span> - Remaining Credits: <span class='text-success'>{remaining_credits:,} </span> - Auto-TopUp:  {top_up_icon}"
            return HttpResponse(msg, status=200, content_type="text/html")
        except:
            msg = "Unable to check, please reload the page."
            return HttpResponse(msg, status=200, content_type="text/html")

class log_view(LoginRequiredMixin, ListView):
    template_name = "dashboard/log_template.html"
    context_object_name = 'logs'
    paginate_by = 10
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    def get_queryset(self):
        current_user = self.request.user
        return Activity.objects.filter(user_id=current_user).order_by('-created_at')

class AllTagListView(LoginRequiredMixin, ListView):
    template_name= "dashboard/tags_list.html"
    context_object_name = 'projects'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_queryset(self):
        current_user = self.request.user
        if current_user.account_type == 'sup':
            return Tag.objects.filter(user=current_user)
        else:
            messages.info(self.request, 'You are not allowed to view that page.')
            return redirect('core:home')

class CreateTagView(LoginRequiredMixin, View):
    def post(self, request):
        tag_title = str(request.POST.get('tag_title')).strip()
        color_code = request.POST.get('colorcode')

        if tag_title == '':
            messages.error(request, 'Please enter a tag title!')
            return redirect('auth:tags_list')

        current_user = request.user
        if current_user.account_type == 'sup':
            Tag.objects.create(user=current_user, tag_name=tag_title, color_code=color_code)
            create_log_activity(current_user,'Tag Created')
            messages.success(request, 'Tags created successfully!')
            return redirect('auth:tags_list')
        else:
            messages.info(request, 'You are not allowed. Contact Support')
        return redirect('core:home')

class UpdateTagView(LoginRequiredMixin, View):
    def post(self, request):
        tag_title = str(request.POST.get('tag_title')).strip()
        tag_id = request.POST.get('tag_id')
        color_code = request.POST.get('colorcode')

        if tag_title == '' or tag_id == '':
            messages.error(request, 'Please enter a tag title!')
            return redirect('auth:tags_list')

        current_user = request.user
        if current_user.account_type == 'sup':
            tags_obj = Tag.objects.get(user=current_user, id=tag_id)
            # Check if tag_title ends with "_TDNR"
            existing_tag_title = tags_obj.tag_name
            if "_tdnr" in existing_tag_title.lower():
                tags_obj.color_code = color_code
                tags_obj.save()
                update_log_activity(current_user,'Tag Updated')
                messages.success(request, 'Color code updated successfully!. You can not update Tags Title ending with "_TDNR".')
                return redirect('auth:tags_list')
            else:
                tags_obj.tag_name = tag_title
                tags_obj.color_code = color_code
                tags_obj.save()
                messages.success(request, 'Tags updated successfully!')
                return redirect('auth:tags_list')
        else:
            messages.info(request, 'You are not allowed. Contact Support')
        return redirect('core:home')

class DeleteTagView(LoginRequiredMixin, View):
    def post(self, request):
        tag_id = request.POST.get('tag_id')

        if tag_id == '':
            messages.error(request, 'Something is wrong!')
            return redirect('auth:tags_list')

        current_user = request.user
        if current_user.account_type == 'sup':
            # Check if tag_title ends with "_TDNR"
            tags_obj = Tag.objects.get(user=current_user, id=tag_id)
            tag_title = tags_obj.tag_name
            if "_tdnr" in tag_title.lower() :
                messages.warning(request, 'Tags ending with "_TDNR" cannot be deleted')
            else:
                tags_obj.delete()  # Delete the tag
                delete_log_activity(current_user,'Delete Tag')
                messages.success(request, 'Tag deleted successfully!')
            return redirect('auth:tags_list')
        else:
            messages.info(request, 'You are not allowed. Contact Support')
        return redirect('core:home')