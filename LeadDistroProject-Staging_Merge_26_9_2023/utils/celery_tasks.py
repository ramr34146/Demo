from django.contrib.auth import get_user_model
from utils.handle_llr import LandlineRemoverAPI

UserModel = get_user_model()

from celery import shared_task

#custom
from dashboard.models import LeadsFile, LeadsFileData
from users.models import SuperUsers
from utils.handle_django import (
        AssignTasks,
        UpdateLeadsPhoneDataTypes,
        handle_td_contact_bulk,
        checkTeamMemberCampaign
    )
from  utils.handle_email import (
    email_SendAfterCSVSuccessfull,
    email_SendAfterCSVFailed,
    email_SendAfterCSVAssigned,
    LeadLimitLowerSendEmail
    )

@shared_task
def celery_handle_td_contact_bulk(leadfile_uid):
    handle_td_contact_bulk(leadfile_uid)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=10, retry_jitter=True, retry_kwargs={'max_retries':5})
def HandleLeadsDataWithAssigned(self, leadfile_uid):
    # import time 
    # time.sleep(2000)

    lead_file_obj = LeadsFile.objects.get(uid=leadfile_uid)
    do_not_distribute = lead_file_obj.is_distribution_block

    if self.request.retries >= self.max_retries:
        try:
            LeadsFile.objects.filter(uid=leadfile_uid).update(status=LeadsFile.FILE_STATUS.FAILED)
            email_SendAfterCSVFailed(lead_file_obj.user.email,lead_file_obj.user.name,lead_file_obj.csvfile_name,leadfile_uid)
        except:pass
        return None

    try:
        UpdateLeadsPhoneDataTypes(leadfile_uid)
        LeadsFile.objects.filter(uid=leadfile_uid).update(status=LeadsFile.FILE_STATUS.COMPLETED)
    except:
        raise Exception()


    if do_not_distribute is False:
        checkTeamMemberCampaign(leadfile_uid)
        AssignTasks(leadfile_uid)
        LeadsFile.objects.filter(uid=leadfile_uid).update(status=LeadsFile.FILE_STATUS.ASSIGNED)
        email_SendAfterCSVAssigned(lead_file_obj.user.email,lead_file_obj.user.name,lead_file_obj.csvfile_name,leadfile_uid)

    try:
        LeadsFileData.objects.filter(lead_file__uid=leadfile_uid).update(is_done=True)
    except: pass

    if do_not_distribute is False:
        try:
            celery_handle_td_contact_bulk(leadfile_uid) 
        except: pass

    try:
        email_SendAfterCSVSuccessfull(lead_file_obj.user.email,lead_file_obj.user.name,lead_file_obj.csvfile_name,leadfile_uid)

        # Team Member have not Leads than Alert Super User and Team Members
        LeadLimitLowerSendEmail(leadfile_uid)
    except:
        pass
