from pyexpat import model
from django.db import models
from django.shortcuts import reverse
from django.conf import settings
import os, json , uuid
from ast import literal_eval as ast_literal_eval
from users.models import SuperUsers, TeamMembers, User
from django.db.models import Q


class Tag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tag_name = models.CharField(verbose_name="Tag Title", max_length=255,default=None,blank=True,null=None)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    color_code = models.CharField(verbose_name="Color Code", max_length=255,default=None,blank=True,null=None)

    def __str__(self):
        return f"{self.tag_name}"

def user_csv_files_upload_path(instance, filename):
    path = "csv_upload_files/"
    extension = "." + filename.split('.')[-1]
    filename_reformat = f"{instance.uid}{extension}"
    return os.path.join(path, filename_reformat)


class LeadsFile(models.Model):
    class FILE_STATUS(models.TextChoices):
        STARTED = 'str', 'Started'
        PROCESSED = 'pro', 'Processing'
        COMPLETED = 'com', 'Completed'
        ASSIGNED = 'ass', 'Distributed'
        FAILED = 'fld', 'Failed'
        CANCELLED = 'can', 'Cancelled'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uid = models.UUIDField(auto_created=True, default = uuid.uuid4, editable = False, unique=True)
    project_name = models.CharField(verbose_name="Project Name", max_length=255, blank=True, null=True)
    project_description = models.TextField(null=True, blank=True)
    csvfile = models.FileField(upload_to=user_csv_files_upload_path)
    csvfile_name = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=3, choices=FILE_STATUS.choices, default=FILE_STATUS.STARTED)
    total_leads = models.IntegerField(default=0)
    team_ids = models.TextField(null=True, blank=True)

    is_llr_allow = models.BooleanField(verbose_name="Allow LLR to Check LineType and DncType", default=True)
    is_dnc_block = models.BooleanField(verbose_name="Block DNC Leads by LLR", default=False)
    is_distribution_block = models.BooleanField(verbose_name="Do Not Distribute Leads", default=False)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    taskid = models.TextField(null=True, blank=True)

    tags = models.CharField(max_length=255, verbose_name='Tag Name', null=True, blank=True, default=None)

    def __str__(self):
        return f"{self.uid}"

    class Meta:
        ordering = ["-created"]
        verbose_name = verbose_name_plural = "Leads Csv File"

    def get_user_obj(self):
        return self.user

    def get_superuser_obj(self):
        return self.user.superusers

    def get_detail_url(self):
        return reverse("auth:lead_details", kwargs={'UID': self.uid})

    def get_file_download_url(self):
        return reverse("auth:lead_file_download", kwargs={'UID': self.uid})

    def return_leadsfiledata_qs(self):
        leadsfiledata_qs = LeadsFileData.objects.filter(lead_file=self).order_by('-created_at')
        return leadsfiledata_qs

    def return_total_assigned_leads(self):
        leadsfiledata_qs = self.return_leadsfiledata_qs().exclude(is_callblock=True).exclude(dnctype__icontains='litigator').exclude(linetype__icontains='landline').exclude(linetype__icontains='invalid')
        if self.is_dnc_block:
            leadsfiledata_qs = leadsfiledata_qs.exclude(dnctype__icontains='dnc')
        return leadsfiledata_qs

    def return_total_leads_skipped(self):
        if self.is_dnc_block:
            leadsfiledata_qs = self.return_leadsfiledata_qs().filter(Q(dnctype__icontains="litigator") | Q(is_callblock=True) | Q(linetype__icontains="landline") | Q(dnctype__icontains="dnc") | Q(dnctype__icontains="invalid"))
        else:
            leadsfiledata_qs = self.return_leadsfiledata_qs().filter(Q(dnctype__icontains="litigator") | Q(is_callblock=True) | Q(linetype__icontains="landline") | Q(dnctype__icontains="invalid"))
        return leadsfiledata_qs

    def return_total_leads_callblock(self):
        leadsfiledata_qs = self.return_leadsfiledata_qs()
        return leadsfiledata_qs.filter(is_callblock=True)
    
    def return_total_leads_litigator(self):
        leadsfiledata_qs = self.return_leadsfiledata_qs()
        return leadsfiledata_qs.filter(dnctype__icontains="litigator")

    def return_total_leads_dnctype(self):
        leadsfiledata_qs = self.return_leadsfiledata_qs()
        return leadsfiledata_qs.filter(dnctype__icontains='dnc')

    def return_total_leads_clean(self):
        leadsfiledata_qs = self.return_leadsfiledata_qs()
        return leadsfiledata_qs.filter(dnctype__icontains='clean', linetype__icontains="mobile")

    def return_team_ids_list(self):
        try:
            teams_ids = self.team_ids
            return ast_literal_eval(teams_ids)
        except: 
            return []

    def return_total_leads_line_type_invalid(self):
        leadsfiledata_qs = self.return_leadsfiledata_qs()
        return leadsfiledata_qs.filter(linetype__icontains="invalid")
    
    @property
    def return_processed_leads(self):
        #helping method using in return_file_status
        leadsfiledata_qs = self.return_leadsfiledata_qs()
        return leadsfiledata_qs.filter(is_ready=True).count() 

    @property
    def return_file_status(self):
        return f"Processing {self.return_processed_leads}/{self.total_leads}"

    @property
    def get_total_leads(self):
        # return self.total_leads
        return self.return_leadsfiledata_qs().count()

    @property
    def get_total_assigned_members(self): return len(self.return_team_ids_list())
    
    @property
    def get_total_assigned_leads(self): return self.return_total_assigned_leads().count()   

    @property
    def get_total_leads_skipped(self): return self.return_total_leads_skipped().count()   

    @property
    def get_total_leads_litigator(self): return self.return_total_leads_litigator().count() 

    @property
    def get_total_leads_callblock(self): return self.return_total_leads_callblock().count()

    @property
    def get_total_leads_dnctype(self): return self.return_total_leads_dnctype().count()

    @property
    def get_total_leads_clean(self): return self.return_total_leads_clean().count()

    @property
    def invalid_leads(self):
        return (self.total_leads - self.return_leadsfiledata_qs().count()) + self.return_total_leads_line_type_invalid().count()




class LeadsFileData(models.Model):
    superuser = models.ForeignKey(SuperUsers, on_delete=models.CASCADE)
    lead_file = models.ForeignKey(LeadsFile,  blank=True, null=True, on_delete=models.CASCADE)
    lead_id = models.UUIDField(auto_created=True, default =  uuid.uuid4, editable = False, unique=True)

    name = models.CharField(verbose_name="Name", max_length=255)
    phone = models.CharField(verbose_name="Phone Number", max_length=255)
    email = models.CharField(verbose_name="Email", max_length=255, null=True, blank=True)
    birthdate = models.CharField(verbose_name="Date of Birth", max_length=255, null=True, blank=True)
    address = models.CharField(verbose_name="Address", max_length=255, null=True, blank=True)
    state = models.CharField(verbose_name="State", max_length=255, null=True, blank=True)
    zipcode = models.CharField(verbose_name="Zip Code", max_length=255, null=True, blank=True)
    custom_field1 = models.CharField(verbose_name="Custom Field 1", max_length=255, null=True, blank=True)
    custom_field2 = models.CharField(verbose_name="Custom Field 2", max_length=255, null=True, blank=True)
    custom_field3 = models.CharField(verbose_name="Custom Field 3", max_length=255, null=True, blank=True)
    custom_field4 = models.CharField(verbose_name="Custom Field 4", max_length=255, null=True, blank=True)
    custom_field5 = models.CharField(verbose_name="Custom Field 5", max_length=255, null=True, blank=True)

    linetype = models.CharField(verbose_name="Line Type", max_length=255, null=True, blank=True)
    dnctype = models.CharField(verbose_name="DNC Type", max_length=255, null=True, blank=True)
    is_callblock = models.BooleanField(verbose_name="Call Block from USH API", default=False)

    is_ready = models.BooleanField(verbose_name="Ready To Assign", default=False)
    is_assigned = models.BooleanField(verbose_name="Assigned To Member", default=False)
    is_done = models.BooleanField(verbose_name="Completed", default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    tags = models.CharField(max_length=255, null=True, blank=True,default=None)
    
    def __str__(self):
        return f"{self.lead_id}"

    class Meta:
        ordering = ["-id"]
        verbose_name = verbose_name_plural ="Leads File Data"

    def get_lead_agent(self):
        return LeadsDistribution.objects.filter(lead=self).first()

    def get_lead_agent_display(self):
        agent = self.get_lead_agent()
        if agent is not None: return agent.assign_to.name
        return 'Not Assigned'

class LeadsDistribution(models.Model):
    assign_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lead = models.ForeignKey(LeadsFileData, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.assign_to.name} - SuperUser ({self.lead.superuser.user.name})"

    class Meta:
        # ordering = ["-id"]
        verbose_name = verbose_name_plural ="Leads Distribution Data"

    def get_member_obj(self):
        return TeamMembers.objects.filter(user=self.assign_to).first()

    @property
    def get_lead_info_display(self):
        return f"{self.lead.phone} | {self.lead.is_callblock} | {self.lead.linetype} | {self.lead.dnctype}"


class Activity(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE,blank=True, null=True,default=None)
    actions = models.CharField(max_length=50, default=None, choices=(
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
    ),blank=True, null=True)
    description = models.TextField(blank=True, null=True,default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)