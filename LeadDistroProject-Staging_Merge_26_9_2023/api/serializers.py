from requests import request
from rest_framework import serializers
from utils.handle_django import (
        CheckEmailExist, 
        returnSuperuserObj, 
        returnTeamMemberObj,
        )
from utils.utils import returnCleanPhone

from dashboard.models import LeadsFileData

class SuperuserSerializer(serializers.Serializer):
    full_name = serializers.CharField(allow_blank=False)
    email = serializers.EmailField(allow_blank=False)
    password = serializers.CharField(allow_blank=False)
    account_type = serializers.CharField(allow_blank=False)
    company_name = serializers.CharField(allow_blank=False)
    region = serializers.CharField(allow_blank=False)
    llr_apikey = serializers.CharField(allow_blank=True)

    def validate_email(self, value):
        value = str(value).strip().lower()
        if CheckEmailExist(value):
            raise serializers.ValidationError('Email is already Exist')
        return value

    def validate_account_type(self, value):
        if value not in ['ush', 'blank']:
            raise serializers.ValidationError('Value should be either ush or blank')
        return str(value).lower()


class TeamMemberSerializer(serializers.Serializer):
    full_name = serializers.CharField(allow_blank=False)
    superuser_email_or_uid = serializers.CharField(allow_blank=False)
    email = serializers.EmailField(allow_blank=False)
    password = serializers.CharField(allow_blank=False)
    textdrip_apikey = serializers.CharField(allow_blank=False)
    textdrip_compaign_id = serializers.CharField(allow_blank=False)
    textdrip_compaign_value = serializers.CharField(allow_blank=False)
    llr_apikey = serializers.CharField(allow_blank=True)

    def validate_email(self, value):
        value = str(value).strip().lower()
        user_obj = returnTeamMemberObj(value)
        if user_obj:
            raise serializers.ValidationError('Teammember is already Exist on this Email or UID')
        return value

class LinkUnlinkTeamMemberSerializer(serializers.Serializer):
    superuser_email_or_uid = serializers.CharField(allow_blank=False)
    teammember_email_or_uid = serializers.EmailField(allow_blank=False)

    def validate_superuser_email_or_uid(self, value):
        user_obj = returnSuperuserObj(value)
        if not user_obj:
            raise serializers.ValidationError('Superuser is not Exist on this Email or UID')
        return user_obj

    def validate_teammember_email_or_uid(self, value):
        user_obj = returnTeamMemberObj(value)
        if not user_obj:
            raise serializers.ValidationError('Teammember is not Exist on this Email or UID')
        return user_obj


class LeadSerializer(serializers.Serializer):
    name = serializers.CharField(allow_blank=False) #req
    phone = serializers.CharField(allow_blank=False) #req
    email = serializers.EmailField(allow_blank=True)
    birthdate = serializers.CharField(allow_blank=True)
    address = serializers.CharField(allow_blank=True)
    state = serializers.CharField(allow_blank=True)
    zipcode = serializers.CharField(allow_blank=True)
    custom_field1 = serializers.CharField(allow_blank=True)
    custom_field2 = serializers.CharField(allow_blank=True)
    custom_field3 = serializers.CharField(allow_blank=True)
    custom_field4 = serializers.CharField(allow_blank=True)
    custom_field5 = serializers.CharField(allow_blank=True)
    tags = serializers.CharField(allow_blank=True)


    def validate_name(self, value):
        return str(value).strip()

    def validate_phone(self, value):
        clean_phone = returnCleanPhone(value)
        if clean_phone is None:
            raise serializers.ValidationError('Phone Number is not valid.')
        return value



