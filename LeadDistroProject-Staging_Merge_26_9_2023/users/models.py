from pyexpat import model
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from uuid import uuid4
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
# User = settings.AUTH_USER_MODEL
from django.shortcuts import reverse

#custom
from utils.utils import generateAPIKEY



class LowercaseEmailField(models.EmailField):
    """
    Override EmailField to convert emails to lowercase before saving.
    """
    def to_python(self, value):
        """
        Convert email to lowercase.
        """
        value = super(LowercaseEmailField, self).to_python(value)
        # Value can be None so check that it's a string before lowercasing.
        if isinstance(value, str):
            return value.lower()
        return value

class UserManager(BaseUserManager):
  def _create_user(self, email, password, is_staff, is_superuser, **extra_fields):
    if not email:
        raise ValueError('User must have an email address')
    now = timezone.now()
    email = self.normalize_email(email).lower()
    user = self.model(
        email=email,
        is_staff=is_staff, 
        is_active=True,
        is_superuser=is_superuser, 
        last_login=now,
        date_joined=now, 
        **extra_fields
    )
    user.set_password(password)
    user.save(using=self._db)
    return user

  def create_user(self, email, password, **extra_fields):
    return self._create_user(email, password, False, False, **extra_fields)

  def create_superuser(self, email, password, **extra_fields):
    user=self._create_user(email, password, True, True, **extra_fields)
    user.save(using=self._db)
    return user


class User(AbstractBaseUser, PermissionsMixin):
    class ACCOUNT_TYPE(models.TextChoices):
      SUPER_USER = 'sup', 'Super User'
      TEAM_MEMBER = 'team', 'Team Member'
      OTHER = 'oth', 'Other Account'

    email = LowercaseEmailField(unique=True)
    name = models.CharField(max_length=254, null=True, blank=True)
    account_type = models.CharField(max_length=5, choices=ACCOUNT_TYPE.choices, default=ACCOUNT_TYPE.OTHER)

    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    is_dark_mode = models.BooleanField(default=True)
    
    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
    
    def __str__(self) -> str:
      return f"{self.email}" 

    @property
    def is_member_account(self):
        if self.account_type == User.ACCOUNT_TYPE.TEAM_MEMBER:
          return True
        return False 

    @property
    def is_superuser_account(self):
        if self.account_type == User.ACCOUNT_TYPE.SUPER_USER:
          return True
        return False 

    @property
    def count_total_projects_uploaded(self):
        return self.leadsfile_set.all().count()


class SuperUsers(models.Model):
    class ACCOUNT_TYPE(models.TextChoices):
      USHADVISOR = 'ush', 'USHA Advisor'
      BLANK = 'bla', 'Blank'
      
    superuser_id = models.UUIDField(auto_created=True, default = uuid4, editable = False, unique=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=254, null=True, blank=True)
    region = models.CharField(max_length=254, null=True, blank=True)
    account_type = models.CharField(max_length=3, choices=ACCOUNT_TYPE.choices, default=ACCOUNT_TYPE.BLANK)
    teams = models.ManyToManyField("TeamMembers", verbose_name="Teams Members", related_name='team_members', blank=True)
    llr_apikey = models.CharField(verbose_name="LandlineRemover APIKEY", max_length=255, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    assign_leads_limit = models.IntegerField(verbose_name="Assign Leads Limit", default=-1,
                                             help_text="-1 for unlimited")

    class Meta:
        verbose_name = "Super User"
        verbose_name_plural = "Super Users"

    def __str__(self) -> str:
      return self.user.email

    def is_usha_account(self):
      if self.account_type == 'ush':
        return True 
      return False 

    @property
    def count_total_team_members(self):
        return self.teams.all().count()


class TeamMembers(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name="Team Account User", on_delete=models.CASCADE)
    team_id = models.UUIDField(auto_created=True, default = uuid4, editable = False, unique=True)
    llr_apikey = models.CharField(verbose_name="LandlineRemover APIKEY", max_length=255, null=True, blank=True)
    vacation_mode = models.BooleanField(verbose_name="Vacation mode", default=False)
    all_states = models.BooleanField(default=True)
    states_list = models.JSONField(verbose_name="States List", default=dict)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
       return self.user.email

    class Meta:
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"

    @property
    def member_of_superusers(self):
        return self.team_members.all()

    def get_member_detail_url(self):
        return reverse("auth:team_member_detail", kwargs={'UID': self.team_id})

    def campaign_data(self):
        cobj = TextDripCampaign.objects.filter(team_member=self)
        if cobj:
            return cobj.first()
        return None

    def return_states_list(self):
        try:
            states = self.states_list
            return ast_literal_eval(states)
        except: 
            return []
        
class LeadsLimitRequest(models.Model):
    class LEADLIMIT_STATUS(models.TextChoices):
      PENDING = 'pending', 'Pending'
      APPROVED = 'approved', 'Approved'
      REJECTED = 'rejected', 'Rejected'

    superuser = models.ForeignKey(SuperUsers, verbose_name='Super User', on_delete=models.CASCADE, default=None, blank=True, null=True)
    team_member = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Team Member', on_delete=models.CASCADE,default=None,blank=True, null=True)
    current_limit = models.PositiveIntegerField(default=None,blank=True, null=True)
    lead_limit_status = models.CharField(max_length=10, choices=LEADLIMIT_STATUS.choices, default=LEADLIMIT_STATUS.PENDING,blank=True, null=True)

    class Meta:
        verbose_name = verbose_name_plural = "Members Lead Limit Request"

class UserProfile(models.Model):
    user = models.OneToOneField(User, primary_key=True, verbose_name='user',
                                related_name='profile', on_delete=models.CASCADE)

    api_key = models.CharField(max_length=40, blank=True, null=True)
    
    is_td_contact = models.BooleanField(verbose_name="Send TD Contacts", default=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} Profile"

    class Meta:
        verbose_name = verbose_name_plural = "User Profile Data"

#import here don't move above
from dashboard.models import LeadsDistribution 

class TextDripCampaign(models.Model):
    team_member = models.ForeignKey(TeamMembers, verbose_name='Team Member', on_delete=models.CASCADE)
    superuser = models.ForeignKey(SuperUsers, verbose_name='Super User', on_delete=models.SET_NULL,  blank=True, null=True)

    textdrip_apikey = models.CharField(max_length=255, null=True, blank=True)
    textdrip_compaign_id =  models.CharField(max_length=255, null=True, blank=True)
    textdrip_compaign_value =  models.CharField(max_length=255, null=True, blank=True)
    
    is_temporary_disabled = models.BooleanField(verbose_name="Temporary Disabled(Paused)", default=False)
    is_campaign_activated = models.BooleanField(default=False)
    assign_leads_limit = models.IntegerField(verbose_name="Assign Leads Limit", help_text="-1 for unlimited",default=0)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.team_member} Under {self.superuser}"

    class Meta:
        verbose_name = verbose_name_plural = "TextDrip Campaign Data"

    @property
    def total_assign_leads(self):
        #leads_data = getMemberRemainingLeadsLimit(obj.team_member.user, obj.superuser)
        leads_data =  LeadsDistribution.objects.filter(assign_to=self.team_member.user, lead__superuser=self.superuser).count()
        return leads_data


class LastTask(models.Model):
    team_member = models.ForeignKey(TeamMembers, verbose_name='Team Member',  on_delete=models.SET_NULL,  blank=True, null=True)
    superuser = models.ForeignKey(SuperUsers, verbose_name='Super User', on_delete=models.SET_NULL,  blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.team_member} Under {self.superuser}"

    class Meta:
        verbose_name = verbose_name_plural = "Last Task"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, api_key=generateAPIKEY())
