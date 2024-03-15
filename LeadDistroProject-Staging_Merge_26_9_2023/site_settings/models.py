from statistics import mode
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save

from maintenance_mode.core import get_maintenance_mode, set_maintenance_mode


class GeneralSettings(models.Model):
    is_maintenance_mode = models.BooleanField(verbose_name="Maintenance Mode", default=False)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
       return "General Settings"

    class Meta:
        verbose_name = verbose_name_plural = "General Settings"



@receiver(post_save, sender=GeneralSettings)
def GeneralSettingsSignals(sender, instance, created, **kwargs):
    set_maintenance_mode(instance.is_maintenance_mode)
    