import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'leads.settings')
app = Celery('leads')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.update(result_expires=10, result_backend='django-db',)
