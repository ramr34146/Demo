from allauth.account.forms import SignupForm
from django import forms
from users.models import SuperUsers
from utils.handle_llr import LandlineRemoverAPI
from utils.handle_django import CheckEmailExist


class CustomSuperUserRegisterForm(SignupForm):
    full_name = forms.CharField(max_length=30, label='Full Name', required=True,  widget=forms.TextInput(attrs={'placeholder': 'Enter Your Full Name'}))
    company_name = forms.CharField(max_length=100, label='Company Name', required=True,  widget=forms.TextInput(attrs={'placeholder': 'Enter Your Company Name'}))
    region = forms.CharField(max_length=100, label='Region ', required=True, widget=forms.TextInput(attrs={'placeholder': 'Enter Your Region'}))
    landline_apikey = forms.CharField(max_length=100, label='LandlineRemover APIkey', required=False, widget=forms.TextInput(attrs={'placeholder': 'Enter Your LandlineRemover APIKey or Leave it Empty '}))

    field_order = ['full_name', 'email', 'password1', 'company_name', 'region', 'landline_apikey']

    def clean_email(self):
        value = str(self.cleaned_data["email"]).lower()
        if CheckEmailExist(value):
            self.add_error("email", "This Email is already Exist. Please Use another valid email address.")
        return value

    def clean_landline_apikey(self):
        llr_apikey = self.cleaned_data.get("landline_apikey", '')
        initial_error = "Please Add Valid LandlineRemover APIKey"
        if len(llr_apikey) == 0: 
            return llr_apikey
        elif len(llr_apikey) == 40:
            llr_obj = LandlineRemoverAPI()
            GetAPIStatus = llr_obj.GetAPIStatus(llr_apikey)
            if not GetAPIStatus:
                self.add_error("landline_apikey", initial_error)
        else:
            self.add_error("landline_apikey", initial_error)
        return llr_apikey


    def save(self, request):
        user = super(CustomSuperUserRegisterForm, self).save(request)
        user.name = self.cleaned_data.get("full_name", '')
        user.account_type = 'sup'
        user.save()
        if '@ushadvisors' in user.email:
            account_type = 'ush'
        else:
            account_type = 'bla'
        SuperUsers.objects.create(
            user = user, 
            company_name =  self.cleaned_data.get("company_name", ''),
            region =  self.cleaned_data.get("region", ''),
            llr_apikey =  self.cleaned_data.get("landline_apikey", ''),
            account_type = account_type
        )
        return user
