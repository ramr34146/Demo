from pathlib import Path
import os
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(os.path.join(BASE_DIR,".env"))

SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = (bool(int(os.environ.get('DEBUG',1))))


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites', 
    
    'import_export',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    "django_htmx",
    "crispy_forms",
    "crispy_bootstrap5",
    "maintenance_mode",
    'django_celery_results',

    'users',
    'api',
    'core',
    'dashboard',
    'site_settings',
    'contact',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django_htmx.middleware.HtmxMiddleware', #3rd party middleware
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "maintenance_mode.middleware.MaintenanceModeMiddleware", #3rd party middleware
]

ROOT_URLCONF = 'leads.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'leads.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

##################### Custom Settings #########################
ADMIN_GLOBAL_APIKEY = str(os.environ.get('ADMIN_GLOBAL_APIKEY')).strip()



##################### Static and Media Files Settings #########################
STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATICFILES_DIRS = [BASE_DIR / "site_assets"]
STATIC_ROOT = BASE_DIR / "static_cdn" / "static" 
MEDIA_ROOT = BASE_DIR / "static_cdn" / "media" 


##################### CrispyTemplateSettings #########################
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


################# Custom User Model + AllAuth ###################
AUTH_USER_MODEL = 'users.User'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend', # existing backend
    'allauth.account.auth_backends.AuthenticationBackend',
)

ACCOUNT_FORMS = {'signup': 'users.forms.CustomSuperUserRegisterForm'}

SITE_ID = 1
LOGIN_URL = '/signin/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED  = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = "mandatory" # "mandatory" #"none"
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 1
ACCOUNT_SIGNUP_EMAIL_ENTER_TWICE = False
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 7
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 600
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = False
ACCOUNT_USERNAME_MIN_LENGTH = 5
ACCOUNT_UNIQUE_EMAIL = True

################# MAINTENANCE MODE ###################
MAINTENANCE_MODE = None
MAINTENANCE_MODE_IGNORE_ADMIN_SITE = True
MAINTENANCE_MODE_IGNORE_SUPERUSER = True
MAINTENANCE_MODE_IGNORE_ANONYMOUS_USER = False
MAINTENANCE_MODE_IGNORE_AUTHENTICATED_USER = False
MAINTENANCE_MODE_IGNORE_STAFF = False
MAINTENANCE_MODE_TEMPLATE = "pages/503.html"
MAINTENANCE_MODE_STATUS_CODE = 503


##################### CELERY & REDIS #########################

CELERY_BROKER_URL = "redis://localhost"
CELERY_RESULT_BACKEND = "redis://localhost"
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
BROKER_CONNECTION_RETRY = True
BROKER_CONNECTION_MAX_RETRIES = 0
BROKER_CONNECTION_TIMEOUT = 360


##################### REST FRAMEWORK SETTINGS #########################

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ]
}
