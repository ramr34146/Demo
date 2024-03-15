from django.shortcuts import redirect, render
from django.views.generic import View
from django.contrib import messages
from allauth.account.admin import EmailAddress
from django.contrib.auth import get_user_model
UserModel = get_user_model()
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse

#custom
from utils.handle_django import returnTeamMemberObj, returnSuperuserObj, CreateALLAuthEmailAddress, getLLRCredits, TeamMemberAcceptInvitation
from utils.handle_textdrip import TextDrip
from utils.utils import is_valid_uuid, generatePassword
from users.models import SuperUsers, TeamMembers, TextDripCampaign, User, UserProfile
from utils.handle_states import states_list
from utils.log import(
    create_log_activity,
    update_log_activity
)
class EditProfileView(View):
    template_name = "users/edit_profile.html"

    def get(self, request, *args, **kwargs): 
        current_user = request.user 
        if current_user.account_type == 'sup':
            context = {
                'is_superuser' : True,
                'superuser' : SuperUsers.objects.get(user=current_user)
            }
        elif current_user.account_type == 'team':
            team_member = TeamMembers.objects.get(user=current_user)
            team_states_list = team_member.states_list

            final_states = {}
            for state_key, state_value in states_list.items():
                if team_states_list.get(state_key) is not None:
                    final_states[state_key] = [state_value, True]
                else:
                    final_states[state_key] = [state_value, False]

            context = {
                'is_teammeber' : True,
                'team_member' : team_member,
                'states_list': final_states,
            }
        else:
            return redirect('core:home')
        return render(request, self.template_name, context)
        
    def post(self, request, *args, **kwargs): 
        current_user = request.user 
        if current_user.account_type == 'sup':
            sp_fullname = self.request.POST.get('sp_fullname')
            sp_company_name = str(self.request.POST.get('sp_company_name')).strip()
            sp_region = str(self.request.POST.get('sp_region')).strip()
            sp_llr_apikey = str(self.request.POST.get('sp_llr_apikey')).strip()
            assign_leads_limit = str(self.request.POST.get('assign_leads_limit')).strip()

            llr_apikey_result = ''

            if len(sp_llr_apikey) == 40:
                api_status_ = getLLRCredits(sp_llr_apikey)
                if api_status_:
                    llr_apikey_result = sp_llr_apikey
                    messages.success(request, f"LandlineRemover APIkey is valid. Remaining Credits: {api_status_:,}")
                else:
                    messages.info(request, "LandlineRemover APIkey is not valid. Please Check again!")
            else:
                messages.info(request, "LandlineRemover APIkey is not valid. Please Check again!")

            current_user.name = sp_fullname
            current_user.save()

            SuperUsers.objects.filter(user=current_user).update(company_name=sp_company_name, region=sp_region,
                                                                llr_apikey=llr_apikey_result,assign_leads_limit=assign_leads_limit)
            update_log_activity(current_user,"Superuser Edit-profile updated successfully")

        elif current_user.account_type == 'team':
            team_fullname = self.request.POST.get('tm_fullname')
            team_llr_apikey = str(self.request.POST.get('tm_llr_apikey')).strip()

            if request.POST.get("all_states", None) is not None: 
                all_states = True
            else:
                all_states = False

            if request.POST.get("vacation_mode", None) is not None: 
                vacation_mode = True
            else:
                vacation_mode = False

            
            state_list_josn = {}
            state_list = self.request.POST.getlist('state_list')
            state_list = [i for i in state_list if i]

            if len(state_list) == 0 and all_states is False:
                all_states = True

            if len(state_list) > 0:
                for state in state_list:
                    state_key, state_value = state.split('_')
                    state_list_josn[state_key] = state_value 

            if len(team_llr_apikey) !=40:
                team_llr_apikey = ''

            current_user.name = team_fullname
            current_user.save()
            TeamMembers.objects.filter(user=current_user).update(llr_apikey=team_llr_apikey, 
                all_states=all_states, 
                states_list=state_list_josn,
                vacation_mode=vacation_mode,
                updated=timezone.now()
                )
            update_log_activity(current_user,"Team member Edit-profile updated successfully")
        messages.info(request, "Account Info has been updated Successfully! ")
        #return redirect('auth:home')
        return redirect('users:edit_profile')


#need to clean it and modify the code
class MemberProcessView(View):
    template_name = "users/member_process.html"

    def get(self, request, *args, **kwargs): 
        superuser_id = request.GET.get('sid')
        member_id = request.GET.get('mid')
        member_apitoken = str(request.GET.get('apiToken')).strip()
        
        if not all([superuser_id, member_id, member_apitoken]): return redirect('auth:home')
        
        if not is_valid_uuid(superuser_id) or not is_valid_uuid(member_id): return redirect('auth:home')

        team_obj = returnTeamMemberObj(member_id)
        superuser_obj = returnSuperuserObj(superuser_id)
        if not team_obj or not superuser_obj:  return redirect('auth:home')

        campaign_obj = TextDripCampaign.objects.filter(team_member=team_obj, superuser=superuser_obj)
        if campaign_obj:
            if campaign_obj.first().is_campaign_activated:
                return render(request, 'users/snippets/campaign_message.html')

        td_obj = TextDrip()
        campaign_data = td_obj.GetCampaignData(auth_token=member_apitoken)
        #print(campaign_data) #debug

        if team_obj:
            #check team user new account or already exist
            context = {
                "campaign_data": campaign_data,
                "superuser_id": superuser_id.strip(),
                "member_id": member_id.strip(),
                "member_apitoken": member_apitoken.strip(),
                "lead_limit": superuser_obj.assign_leads_limit
            }
            is_team_obj_new = EmailAddress.objects.filter(user=team_obj.user)
            if not is_team_obj_new:
                context['is_member_new'] = True
                context['full_name'] = team_obj.user.name

            return render(request, self.template_name, context)
        return render(request, self.template_name, {})


    def post(self, request, *args, **kwargs): 
        current_user = request.user

        campaign = self.request.POST.get('td_campaign')
        textdrip_compaign_id , textdrip_compaign_value = campaign.rsplit('__')
        superuser_id = str(self.request.POST.get('superuser_id')).strip()
        member_id = str(self.request.POST.get('member_id')).strip()
        member_apitoken = str(self.request.POST.get('member_apitoken')).strip()
        update_leads_limit = int(self.request.POST.get('update_leads_limit', -1))
        
        # print(textdrip_compaign_id) #debug
        # print(textdrip_compaign_value) #debug
        # return render(request, 'users/snippets/campaign_message.html') #debug

        team_obj = returnTeamMemberObj(member_id)
        superuser_obj = returnSuperuserObj(superuser_id)

        if not team_obj or not superuser_obj:  return redirect('auth:home')

        campaign_obj = TextDripCampaign.objects.filter(team_member=team_obj, superuser=superuser_obj)
        if campaign_obj:
            campaign_obj = campaign_obj.first()
            if campaign_obj.is_campaign_activated:
                return render(request, 'users/snippets/campaign_message.html')


        #for new user
        full_name = str(self.request.POST.get('full_name','')).strip()
        user_password = str(self.request.POST.get('user_password','')).strip()
        llr_apikey = '' #str(self.request.POST.get('llr_apikey','')).strip()

        if all([full_name, user_password]):
            is_team_obj_new = EmailAddress.objects.filter(user=team_obj.user)
            if not is_team_obj_new:
                team_user_obj = UserModel.objects.get(email=team_obj.user.email)
                team_user_obj.name = full_name
                team_user_obj.set_password(user_password)
                team_user_obj.save()
                CreateALLAuthEmailAddress(team_user_obj,team_user_obj.email)

        if llr_apikey:
            team_obj.llr_apikey = llr_apikey
            team_obj.save()
        #end for new user

        if superuser_obj.assign_leads_limit == -1 or update_leads_limit < 0:
            if update_leads_limit < 0:
                update_leads_limit = superuser_obj.assign_leads_limit
        elif update_leads_limit > superuser_obj.assign_leads_limit:
            update_leads_limit = superuser_obj.assign_leads_limit



        # updating campaign obj for existing and new user
        if campaign_obj:
            campaign_obj.textdrip_apikey = member_apitoken
            campaign_obj.textdrip_compaign_id = textdrip_compaign_id
            campaign_obj.textdrip_compaign_value = textdrip_compaign_value
            campaign_obj.is_campaign_activated = True
            campaign_obj.save()
        else:
            TextDripCampaign.objects.create(
                team_member=team_obj,
                superuser=superuser_obj,
                textdrip_apikey=member_apitoken,
                textdrip_compaign_id=textdrip_compaign_id,
                textdrip_compaign_value=textdrip_compaign_value,
                is_campaign_activated=True,
                assign_leads_limit=update_leads_limit
            )
            create_log_activity(current_user,"Team Member accept invitation and signup successfully")
        superuser_obj.teams.add(team_obj)
        superuser_obj.save()
        TeamMemberAcceptInvitation(superuser_obj,team_obj)


        messages.info(request, "Account Info has been saved Successfully! You can now login into your account.")
        return redirect('account_login')



class LDIntegrationView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs): 
        redirect_url = request.GET.get('redirect')
        if not redirect_url:
            messages.info(request, "No Valid Integration Url Found")
            return redirect('auth:home')
             
        current_user = request.user
        if current_user.account_type != 'sup':
            messages.info(request, "You need a Superuser Account to use this. Please Contact to Support Team")
            return redirect('auth:home')
        
        api_key = UserProfile.objects.values('api_key').get(user=current_user)['api_key']
        redirect_url = redirect_url + f"&apikey={api_key}"
        return redirect(redirect_url)

    def post(self, request, *args, **kwargs): 
        return redirect('auth:home')

@method_decorator(csrf_exempt, name='dispatch')
class UpdateThemePreferenceView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        current_user = self.request.user
        team_user_obj = UserModel.objects.get(email=current_user)
        is_dark = team_user_obj.is_dark_mode
        if is_dark:
            theme_mode = "theme-dark"
            return JsonResponse({'theme': theme_mode})
        else:
            theme_mode = "theme-light"
            return JsonResponse({'theme': theme_mode})

    def post(self, request, *args, **kwargs):
        theme_mode = request.POST.get('mode')
        if theme_mode == 'theme-light':
            request.user.is_dark_mode = False
            request.user.save()
            theme = "theme-light"
            return JsonResponse({'status': '200', 'theme' : theme})
        else:
            request.user.is_dark_mode = True
            request.user.save()
            theme = "theme-dark"
            return JsonResponse({'status': '200', 'theme' : theme})