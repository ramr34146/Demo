from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .manager import UserManager


# Create your models here.
class CustomUser(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=20, default='f')
    last_name = models.CharField(max_length=20, default='l')
    email = models.EmailField(db_index=True, unique=True)
    name = models.CharField(max_length=50, null=True, blank=True)
    token = models.CharField(max_length=50, default='032a49d9-61f0-436a-8481-31d1ab66711b')
    is_verified = models.BooleanField(default=False)
    verification_otp = models.CharField(max_length=6, null=True, blank=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


class ParaphraseData(models.Model):
    input_tax = models.CharField(max_length=2000, blank=True, null=True, default=None)
    result_tax = models.JSONField(blank=True, null=True, default=None)
    select_tax = models.CharField(max_length=2000, blank=True, null=True, default=None)


class Archive(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    result = models.TextField()


class Synonyms(models.Model):
    word = models.CharField(max_length=250)
    synonyms_list = models.JSONField(max_length=250, blank=True, null=True)


class DataCollection(models.Model):
    words = models.JSONField(max_length=500, blank=True, null=True)
    pos = models.CharField(max_length=20, blank=True, null=True)


class SpinParaphrase(models.Model):
    input_text = models.TextField(blank=True, null=True)
    output_text = models.TextField(blank=True, null=True)
