import email
from django.conf import settings
from django.contrib.auth import get_user_model
UserModel = get_user_model()
from django.db import connection
import json, csv
from django.http import HttpResponse, StreamingHttpResponse, FileResponse, Http404
from django.http import JsonResponse

from rest_framework import views, status, serializers, generics
from rest_framework.response import Response

from .serializers import (
        SuperuserSerializer, 
        TeamMemberSerializer, 
        LinkUnlinkTeamMemberSerializer, 
        LeadSerializer,
    )


from users.models import SuperUsers, TeamMembers, TextDripCampaign, UserProfile
from dashboard.models import LeadsFileData, LeadsFile, LeadsDistribution
from utils.handle_django import (
        CreateALLAuthEmailAddress, 
        CreateUserAccount, 
        returnSuperuserObj,
        API_GetPhoneTypeData, 
        API_AssignTask,
    )
from utils.handle_email import sendEmailWithFile

def returnErrorMSG(msg):
    return {'error': msg}


#working 
class CheckDatabaseDRFAPI(views.APIView,):
    def get(self, request, *args, **kwargs):
        try:
            connection.ensure_connection()
            return Response(status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#working 
class CreateSuperuserDRFAPI(views.APIView,):
    def post(self, request, *args, **kwargs):
        authorized_token = settings.ADMIN_GLOBAL_APIKEY
        if authorized_token != request.headers.get('Authorization'):
            raise serializers.ValidationError(returnErrorMSG('You are not Authroized'))

        request_data = json.loads(request.body.decode('utf-8'))
        serializer = SuperuserSerializer(data=request_data)
        if serializer.is_valid():
            data = serializer.validated_data
            try:
                user_obj = CreateUserAccount(name=data['full_name'], email=data["email"], password=data["password"], account_type='sup')
                superuser = SuperUsers(user = user_obj, 
                                        company_name = data['company_name'], 
                                        region = data['region'], 
                                        llr_apikey = data['llr_apikey'])

                if data['account_type'] == 'ush' or '@ushadvisors' in data["email"]:
                    superuser.account_type = SuperUsers.ACCOUNT_TYPE.USHADVISOR
                superuser.save()
                CreateALLAuthEmailAddress(user_obj=user_obj, email=data['email'])
                return Response({'data': 'SuperUser has been created Successfully'}, status=status.HTTP_201_CREATED)
            except:
                pass
        return Response({"error":"Something is Wrong. Please Contact to Support", 'details':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

#working
class CreateTeamMemberDRFAPI(views.APIView,):
    def post(self, request, *args, **kwargs):
        authorized_token = settings.ADMIN_GLOBAL_APIKEY
        if authorized_token != request.headers.get('Authorization'):
            raise serializers.ValidationError(returnErrorMSG('You are not Authroized'))

        request_data = json.loads(request.body.decode('utf-8'))
        serializer = TeamMemberSerializer(data=request_data)
        if serializer.is_valid():
            data = serializer.validated_data
            superuser_obj = returnSuperuserObj(data['superuser_email_or_uid'])
            if not superuser_obj:
                raise serializers.ValidationError(returnErrorMSG('Superuser is not Exist on this Email or UID'))
            
            try:
                if superuser_obj.user.email == data['email'] or superuser_obj.superuser_id == data['email']: 
                    team_user_obj = TeamMembers.objects.create(user = superuser_obj.user)
                else:
                    user_obj = CreateUserAccount(name=data['full_name'], email=data["email"], password=data["password"], account_type='team')
                    team_user_obj = TeamMembers.objects.create(user = user_obj, llr_apikey=data['llr_apikey'])
                    CreateALLAuthEmailAddress(user_obj=user_obj, email=data['email'])

                TextDripCampaign.objects.get_or_create(
                    team_member = team_user_obj,
                    superuser = superuser_obj, 
                    defaults= {
                        "textdrip_apikey" : data["textdrip_apikey"], 
                        "textdrip_compaign_id" : data["textdrip_compaign_id"],
                        "textdrip_compaign_value" : data["textdrip_compaign_value"],
                        "is_campaign_activated": True
                    })

                superuser_obj.teams.add(team_user_obj)
                superuser_obj.save()
                return Response({'data': 'Team Member has been Created and Assigned to Superuser Successfully!'}, status=status.HTTP_201_CREATED)
            except:
                pass
        return Response({"error":"Something is Wrong. Please Contact to Support", 'details':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

#working
class LinkTeamMemberDRFAPI(views.APIView,):
    def post(self, request, *args, **kwargs):
        authorized_token = settings.ADMIN_GLOBAL_APIKEY
        if authorized_token != request.headers.get('Authorization'):
            raise serializers.ValidationError(returnErrorMSG('You are not Authroized'))

        request_data = json.loads(request.body.decode('utf-8'))
        serializer = LinkUnlinkTeamMemberSerializer(data=request_data)
        if serializer.is_valid():
            data = serializer.validated_data
            superuser_obj = data['superuser_email_or_uid']
            team_user_obj = data['teammember_email_or_uid']

            superuser_obj.teams.add(team_user_obj)
            superuser_obj.save()

            try:
                TextDripCampaign.objects.filter(team_member=team_user_obj, superuser=superuser_obj).update(is_campaign_activated=True)
            except:
                pass

            return Response({'data': 'Team Member has been Linked Successfully!'}, status=status.HTTP_201_CREATED)

        if serializer.errors:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error":"Something is Wrong. Please Contact to Support"}, status=status.HTTP_400_BAD_REQUEST)

#working
class UnlinkTeamMemberDRFAPI(views.APIView,):
    def post(self, request, *args, **kwargs):
        authorized_token = settings.ADMIN_GLOBAL_APIKEY
        if authorized_token != request.headers.get('Authorization'):
            raise serializers.ValidationError(returnErrorMSG('You are not Authroized'))

        request_data = json.loads(request.body.decode('utf-8'))
        serializer = LinkUnlinkTeamMemberSerializer(data=request_data)
        if serializer.is_valid():
            data = serializer.validated_data
            superuser_obj = data['superuser_email_or_uid']
            team_user_obj = data['teammember_email_or_uid']

            superuser_obj.teams.remove(team_user_obj)
            superuser_obj.save()

            try:
                TextDripCampaign.objects.filter(team_member=team_user_obj, superuser=superuser_obj).update(is_campaign_activated=False)
            except:
                pass

            return Response({'data': 'Team Member has been Unlinked Successfully!'}, status=status.HTTP_201_CREATED)

        if serializer.errors:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error":"Something is Wrong. Please Contact to Support"}, status=status.HTTP_400_BAD_REQUEST)


#working
class CreateLeadDRFAPI(views.APIView,):
    def post(self, request, *args, **kwargs):
        user_apikey =  request.headers.get('APIKey')
        
        try:
            request_data = json.loads(request.body.decode('utf-8'))
        except:
            raise serializers.ValidationError(returnErrorMSG('data is not proper formatted.'))

        userprof_obj = UserProfile.objects.filter(api_key=user_apikey)
        if not userprof_obj:
            raise serializers.ValidationError(returnErrorMSG('You are not Authroized! Please Check your APIKey'))
        
        # checking team with all disable options
        superuser_obj = SuperUsers.objects.get(user=userprof_obj.first().user)
        teams_qs = superuser_obj.teams.all()

        team_ids = [str(uid['team_id']) for uid in teams_qs.filter(vacation_mode=True).values('team_id')]
        # print(team_ids)

        disable_ids = [str(uid['team_member__team_id']) for uid in  TextDripCampaign.objects.filter(superuser=superuser_obj).filter(is_temporary_disabled=True).values('team_member__team_id')]
        # print(disable_ids)
        
        exclude_team_ids = list(set(team_ids+disable_ids))
        teams = superuser_obj.teams.all().exclude(team_id__in=exclude_team_ids)
        
        if teams.count() < 1:
            return Response({"error":"There is No Active Team Member in your list"}, status=status.HTTP_400_BAD_REQUEST)
                    
        # print(teams)

        serializer = LeadSerializer(data=request_data)
        if serializer.is_valid():
            data = serializer.validated_data
            data['superuser'] = superuser_obj
            
            lead_obj = LeadsFileData.objects.create(**data)

            try:

                lead_obj.is_callblock, lead_obj.linetype, lead_obj.dnctype = API_GetPhoneTypeData(superuser_obj, data['phone'])
                lead_obj.is_ready = True

                linetype = str(lead_obj.linetype).lower()

                skip_lead = False

                if 'invalid' in linetype:
                    skip_lead = True
                    short_msg = "Number is Invalid"

                elif lead_obj.is_callblock == True:
                    skip_lead = True
                    short_msg = "Number is under Call Block"

                elif 'litigator' in str(lead_obj.dnctype).lower():
                    short_msg = "Number is under DNC Litigator Type"
                    skip_lead = True

                elif 'dnc' in str(lead_obj.dnctype).lower():
                    short_msg = "Number is under DNC Type"
                    skip_lead = True

                elif 'landline' in linetype:
                    short_msg = "Number is Landline"
                    skip_lead = True

                if skip_lead:    
                    lead_obj.is_done = True 
                    lead_obj.save()        
                    return Response({'data': f'Lead has been Skipped | {short_msg}'}, status=status.HTTP_201_CREATED)
                    #return Response({'data': f'Lead has been Skipped | Either Number is in CallBlock or Invalid or Landine or its under DNC/Litigator'}, status=status.HTTP_201_CREATED)

                lead_is_assigned = API_AssignTask(one_lead_obj=lead_obj, superuser_obj=superuser_obj, team_members_qs=teams)


                if not lead_is_assigned:    
                    short_msg = "Either AssignLimit is 0 or state not allowed"
                    lead_obj.is_done = True 
                    lead_obj.save()        
                    return Response({'data': f'Lead has been Skipped | {short_msg}'}, status=status.HTTP_201_CREATED)
                 
                lead_obj.is_assigned = True 
                lead_obj.is_done = True 
                lead_obj.save()
                
                return Response({'data': 'Lead has been Created and Assigned to Team Member!'}, status=status.HTTP_201_CREATED)
            except: 
                pass 
        if serializer.errors:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error":"Something is Wrong. Please Contact to Support"}, status=status.HTTP_400_BAD_REQUEST)


# private user - check user account existance and type
class CheckUserAccount(views.APIView):
    def post(self, request, *args, **kwargs):
        authorized_token = settings.ADMIN_GLOBAL_APIKEY
        if authorized_token != request.headers.get('Authorization'):
            raise serializers.ValidationError(returnErrorMSG('You are not Authroized'))

        try:
            request_data = json.loads(request.body.decode('utf-8'))
        except:
            return Response({"error":"data is not properly formatted"}, status=status.HTTP_400_BAD_REQUEST)

        user_email = request_data['email']

        try:
            user_obj = UserModel.objects.get(email=user_email)
        except:
            return Response({"error":"user not found"}, status=status.HTTP_400_BAD_REQUEST)


        try:
            team_obj = TeamMembers.objects.get(user__email = user_email)
            is_also_team_member = True 
        except: 
            is_also_team_member = False 
       

        responseData = {
            "status": "success",
            "data": {
                'account_type': user_obj.get_account_type_display().lower(),
                'is_also_team_member': is_also_team_member,
            }
        }
      
        return Response(responseData, status=status.HTTP_200_OK)


class DummyFile:
    def write(self, value_to_write):
        return value_to_write



def handle_exceptions(func):
    def wrapper(request, *args, **kwargs):
        try:
            result = func(request, *args, **kwargs)
        except Exception as e:
            return Response("something went wrong. please contact the developer")
    return wrapper


class GenerateUserReport(views.APIView):
    def get(self, request, *args, **kwargs):
        admin_apikey = request.query_params.get('apikey', None)
        send_email = True if request.query_params.get('email', None) == 'true' else False
        output = request.query_params.get('output', 'json') #json, csv
        only_usha = True if request.query_params.get('only_usha', None) == 'true' else False

        authorized_token = settings.ADMIN_GLOBAL_APIKEY
        if authorized_token != admin_apikey:
            raise serializers.ValidationError(returnErrorMSG('You are not Authroized'))

        if only_usha:
            superusers_qs = SuperUsers.objects.filter(account_type=SuperUsers.ACCOUNT_TYPE.USHADVISOR)
        else:
            superusers_qs = SuperUsers.objects.all()

        data = []
        for superuser in superusers_qs:
            rec = {
                'super_user_email': superuser.user.email,
                'super_user_type': superuser.get_account_type_display()
            }
            campaign_qs = TextDripCampaign.objects.filter(superuser=superuser).values('team_member__user__email',
                                'textdrip_apikey',
                                'textdrip_compaign_id',
                                'textdrip_compaign_value',
                                'is_temporary_disabled',
                                'is_campaign_activated',
                                'assign_leads_limit',
                                # 'created',
                                # 'updated',
                            )
            members = []
            for crecord in campaign_qs[:]:
                crecord['team_member_email'] = crecord['team_member__user__email']
                crecord.pop('team_member__user__email')
                members.append(crecord)
            rec['team_members'] = members
            data.append(rec)

        if output == 'csv':
            rows = []
            for data_ in data[:]:
                if len(data_['team_members']) < 1:
                    rows.append(
                        [
                            data_['super_user_email'],
                            data_['super_user_type'],
                        ] 
                    )
                for index, mem in enumerate(data_['team_members'], start=1):
                    if index ==1:
                        rows.append(
                            [
                                data_['super_user_email'],
                                data_['super_user_type'],
                                mem['team_member_email'],
                                mem['textdrip_apikey'],
                                mem['textdrip_compaign_id'],
                                mem['textdrip_compaign_value'],
                                mem['is_temporary_disabled'],
                                mem['is_campaign_activated'],
                                mem['assign_leads_limit'],
                            ] 
                        )
                    else:
                        rows.append(
                            [
                                "",
                                "",
                                mem['team_member_email'],
                                mem['textdrip_apikey'],
                                mem['textdrip_compaign_id'],
                                mem['textdrip_compaign_value'],
                                mem['is_temporary_disabled'],
                                mem['is_campaign_activated'],
                                mem['assign_leads_limit'],
                            ] 
                        )

            rows.insert(0, ['super_user_email', 
                            'super_user_type', 
                            'team_member_email', 
                            'textdrip_apikey',
                            'textdrip_compaign_id', 
                            'textdrip_compaign_value', 
                            'is_temporary_disabled', 
                            'is_campaign_activated', 
                            'assign_leads_limit'
                            ])
         
            if not send_email:
                writer = csv.writer(DummyFile(), delimiter=',')
                data = [writer.writerow(row) for row in rows]
                response = StreamingHttpResponse(data, content_type="text/csv")
                response['Content-Disposition'] = f'attachment; filename="user_report.csv"'
                return response

            with open('user_report.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                for row in rows:
                    writer.writerow([column for column in row])

        if send_email:
            if output == 'csv':
                filename = 'user_report.csv'
            else:
                filename = 'user_report.json'
                with open(filename, 'w') as f: json.dump(data, f)

            send_email_status = sendEmailWithFile(filename, )
            if not send_email_status: return Response(returnErrorMSG('Email Sent Failed'))
            responseData = {
                    "status": "success",
                    "message": "File has been Emailed!"
                }
            return Response(responseData, status=status.HTTP_200_OK)
                

        responseData = {
            "status": "success",
            "data": data
        }
        return Response(responseData, status=status.HTTP_200_OK)

