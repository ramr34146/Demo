import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(os.path.join(BASE_DIR,".env"))

SITE_DOMAIN_LINK = 'https://staging-ld.textdrip.com'

ALLOWED_HOSTS = ['staging_ld.textdrip.com']

DATABASES = {
        'default': 
            {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': str(os.environ.get('DATABASE_NAME')).strip(),
                'USER': str(os.environ.get('DATABASE_USER')).strip(),
                'PASSWORD': str(os.environ.get('DATABASE_PASSWORD')).strip(),
                'HOST': str(os.environ.get('DATABASE_HOST')).strip(),
                'PORT': os.environ.get('DATABASE_PORT'),
            }
    }


################### Email Settings for AWS SES #########################
EMAIL_BACKEND = 'django_smtp_ssl.SSLEmailBackend'
EMAIL_HOST = "email-smtp.us-east-1.amazonaws.com"
EMAIL_PORT = 465
EMAIL_HOST_USER = str(os.environ.get('EMAIL_HOST_USER')).strip()
EMAIL_HOST_PASSWORD = str(os.environ.get('EMAIL_HOST_PASSWORD')).strip()
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = "no-reply@textdrip.com"
