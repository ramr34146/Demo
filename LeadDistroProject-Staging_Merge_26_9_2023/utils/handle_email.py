from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from_email = settings.DEFAULT_FROM_EMAIL
from django.urls import reverse
from django.db.models import Sum
from dashboard.models import LeadsFile
from users.models import TextDripCampaign

#test email
def sendTestEmail(email_send_to='tj@textdrip.com'):
    subject = "test mail"
    message = f"""Thank you for using LandlineRemover.com \n this is test email"""
    return send_mail(subject,message, settings.DEFAULT_FROM_EMAIL, [email_send_to], fail_silently=False)


def sendEmailWithFile(filename, to_email='ahmad@textdrip.com'):
    try:
        subject = 'Automated User Generated Report'
        message = 'Report file has been attached.'
        email_message = EmailMessage(subject, message, from_email, [to_email,])

        # Attach the JSON file to the email message
        with open(filename, 'rb') as f:
            email_message.attach(filename, f.read(), 'application/json')

        # Send the email
        email_message.send()

        return True
    except:
        return False

# function for sending email after csv success
def email_SendAfterCSVSuccessfull(superuser_email, superuser_name, filename, leadfile_uid):
    subject = f'Notification: Your file is successfully completed'

    download_file_url = settings.SITE_DOMAIN_LINK + reverse("auth:lead_details",
                                                            kwargs={'UID': leadfile_uid})

    context = {'superuser': superuser_name,
               'filename': filename,
               'download_url': download_file_url
               }

    html_message = render_to_string('pages/mails/csv_success.html', context)
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, plain_message, from_email, [superuser_email], html_message=html_message)


# function for sending email after csv failed
def email_SendAfterCSVFailed(superuser_email, superuser_name, filename, leadfile_uid):
    subject = f'Notification: Your file is failed to process!'
    download_file_url = settings.SITE_DOMAIN_LINK + reverse("auth:lead_details",
                                                            kwargs={'UID': leadfile_uid})
    context = {'superuser': superuser_name,
               'filename': filename,
               'download_url': download_file_url
               }

    html_message = render_to_string('pages/mails/csv_failed.html', context)
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, plain_message, from_email, [superuser_email], html_message=html_message)


# function for sending email after csv ASSIGNED assigned
def email_SendAfterCSVAssigned(superuser_email, superuser_name, filename, leadfile_uid):
    subject = f'Notification: Your file is Assigned!'
    download_file_url = settings.SITE_DOMAIN_LINK + reverse("auth:lead_details",
                                                            kwargs={'UID': leadfile_uid})
    context = {'superuser': superuser_name,
               'filename': filename,
               'download_url': download_file_url
               }

    html_message = render_to_string('pages/mails/csv_assigned.html', context)
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, plain_message, from_email, [superuser_email], html_message=html_message)

# Team Member have not Leads than Send Mail to  Super User and Team Members
def LeadLimitLowerSendEmail(leadfile_uid):
    lead_file_obj = LeadsFile.objects.get(uid=leadfile_uid)
    superuser_obj = lead_file_obj.get_superuser_obj()
    team_members_qs = superuser_obj.teams.all().filter(team_id__in=lead_file_obj.return_team_ids_list()).order_by('pk')
    textdripCampaign_obj = TextDripCampaign.objects.filter(superuser=superuser_obj)

    if textdripCampaign_obj.filter(assign_leads_limit=-1).count() == 0:
        total_assign_leads_limit = textdripCampaign_obj.aggregate(total_assign_leads_limit=Sum('assign_leads_limit')).get('total_assign_leads_limit', 0)

        if lead_file_obj.total_leads > total_assign_leads_limit:

            email_list = [team_member.user.email for team_member in team_members_qs]
            if email_list:
                subject = "Assign Leads Limit"
                email_addresses_string = ', '.join(email_list)
                context = {
                    'team_members_email': email_addresses_string,  # Join the email addresses with commas
                }
                html_message = render_to_string('pages/superuser_notify_mail.html', context)
                plain_message = strip_tags(html_message)
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = superuser_obj.user.email  # Send the email to the superuser
                send_mail(subject, plain_message, from_email, [recipient_list], html_message=html_message, fail_silently=False)

                # Send email to the team members to limit is 0
                for email_addresses in email_list:
                    subject = "Your Limit is Exceeded"
                    context = {
                        'superuser_email': superuser_obj.user.email,
                    }
                    html_message = render_to_string('pages/team_member_notify_mail.html', context)
                    plain_message = strip_tags(html_message)
                    from_email = settings.DEFAULT_FROM_EMAIL
                    recipient_list = email_addresses  # Send the email to the Team Member
                    send_mail(subject, plain_message, from_email, [recipient_list], html_message=html_message, fail_silently=False)

# function for sending email campaign is invalid
def InvalidCampaignAlertSuperUserSendEmail(superuser_email, team_obj):
    team_email_str = ', '.join(team_obj)
    subject = f'Update campaign'
    context = {'member_email': team_email_str}

    html_message = render_to_string('pages/mails/invalid_campaign_alert_superUser.html', context)
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, plain_message, from_email, [superuser_email], html_message=html_message, fail_silently=False)


def InvalidCampaignAlertTeamMemberSendEmail(superuser_email, team_email,data):
    subject = f'Update campaign'
    context = {'superuser_email': superuser_email}



    superuser_id = data.get('superuser_id', '')
    member_id = data.get('member_id', '')
    redirect_url = data.get('redirect_url')

    context[
        'invitation_link'] = f"https://app.textdrip.com/tauth?redirect=https%3A%2F%2F{redirect_url}%2Fmember-process%2F%3Fmid%3D{member_id}%26sid%3D{superuser_id}"

    html_message = render_to_string('pages/mails/invalid_campaign_alert_teamMember.html', context)
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, plain_message, from_email, [team_email], html_message=html_message, fail_silently=False)