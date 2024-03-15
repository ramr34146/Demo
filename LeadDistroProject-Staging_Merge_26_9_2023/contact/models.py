from django.db import models

class ContactUs(models.Model):
    name = models.CharField(max_length=60)
    email = models.EmailField()
    subject = models.CharField(max_length=100, default='general query', null=True, blank=True)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user_ipaddress = models.TextField(verbose_name="User IpAddress", null=True, blank=True)
    user_os = models.CharField(verbose_name="User OS", max_length=100, null=True, blank=True)
    is_solved = models.BooleanField(verbose_name="Is Solved ?", default=False)
    
    def __str__(self):
        return f"{self.user_ipaddress} - {self.email}"

    class Meta:
        verbose_name = 'Contact Us'
        verbose_name_plural = 'Contact Us'


class FeedBack(models.Model):
    name = models.CharField(max_length=60)
    email = models.EmailField()
    subject = models.CharField(max_length=100, default='general query', null=True, blank=True)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user_ipaddress = models.TextField(verbose_name="User IpAddress", null=True, blank=True)
    user_os = models.CharField(verbose_name="User OS", max_length=100, null=True, blank=True)
    def __str__(self):
        return f"{self.user_ipaddress} - {self.email}"

    class Meta:
        verbose_name = 'FeedBack'
        verbose_name_plural = 'FeedBack'