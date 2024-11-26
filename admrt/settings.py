import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = True

ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
# SECURE_SSL_REDIRECT = True
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CSRF_TRUSTED_ORIGINS = [
    'https://dvuysrcv6p.us-east-1.awsapprunner.com',
    'https://dev-api.admrt.com',
    'https://admrt.com',
    'https://www.admrt.com',
    'https://dev.admrt.com',
    'https://*.admrt.com',
]

CSRF_COOKIE_SECURE = True
# Application definition

INSTALLED_APPS = [
     'daphne' , 
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'djoser',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'storages',
    'newChat',
    'core',
    'channels',
    'softdelete',
    'users',
    'ad_space',
    'chat',
]
ASGI_APPLICATION = 'admrt.asgi.application'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'admrt.middleware.LogRequestMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',

    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'admrt.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / "core/templates",
        ],
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

WSGI_APPLICATION = 'admrt.wsgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# DB_KEY = os.environ.get('DB_KEY')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT', '5432')

DATABASES = {
    'sqlite3': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'postgres': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgres',
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    },
    'local-postgres': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('LOCAL_DB_NAME', 'postgres'),
        'USER': os.getenv('LOCAL_DB_USER', 'admrt'),
        'PASSWORD': os.getenv('LOCAL_DB_PASSWORD', '1234'),
        'HOST': os.getenv('LOCAL_DB_HOST', 'localhost'),
        'PORT': os.getenv('LOCAL_DB_PORT', '5432'),
    },
}


DB_KEY = os.environ.get('DB_KEY') if (os.environ.get('DB_KEY') is not None and os.environ.get('DB_KEY') in DATABASES) else 'sqlite3'
DATABASES['default'] = DATABASES[DB_KEY]


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    # {
    #     'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'core.User'

REST_FRAMEWORK = {
    'COERCE_DECIMAL_TO_STRING': False,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '50/day',
        'user': '5000/day',
    },
}

SIMPLE_JWT = {
   'AUTH_HEADER_TYPES': ('JWT',),
   "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
   "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
   "TOKEN_OBTAIN_SERIALIZER": "core.serializers.TokenObtainPairSerializer"
}

DJOSER = {
    'SERIALIZERS': {
        'user_create': 'core.serializers.UserCreateSerializer',
        'current_user': 'core.serializers.UserSerializer',
        'user': 'core.serializers.UserSerializer',
        'password_reset': 'djoser.serializers.SendEmailResetSerializer',
        'password_reset_confirm': 'djoser.serializers.PasswordResetConfirmSerializer',
        'password_change': 'djoser.serializers.SetPasswordSerializer',
    },
    'EMAIL': {
        'password_reset': 'djoser.email.PasswordResetEmail',
    },
    'PASSWORD_RESET_CONFIRM_URL': 'password/reset/confirm/{uid}/{token}',
    # 'ACTIVATION_URL': 'activate/{uid}/{token}',
    'SEND_ACTIVATION_EMAIL': False,
    'SEND_CONFIRMATION_EMAIL': False,
    'PASSWORD_RESET_CONFIRM_RETYPE': True,
    'PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND': True,
    # 'USER_CREATE_PASSWORD_RETYPE': True,
    'LOGOUT_ON_PASSWORD_CHANGE': False,
}

# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

# global constants for the project
K_SPACE_HOST_ID = 'space_host'
K_ADVERTISER_ID = 'advertiser'

K_SOCIAL_MEDIAS = {
    'fb': 'Facebook',
    'yt': 'YouTube',
    'ln': 'LinkedIn',
    'in': 'Instagram',
    'x': 'X',
    'tt': 'TikTok',
    'wa': 'WhatsApp',
}

K_AD_TYPES = {
    'Print': 'Print',
    'Transportation': 'Transportation',
    'Event': 'Event',
    'Email': 'Email',
    'SMS': 'SMS',
    'Other': 'Other',
}

K_AD_TYPE_FILTERS = {
    'print': 'Print',
    'transportation': 'Transportation',
    'event': 'Event',
    'email': 'Email',
    'sms': 'SMS',
    'other': 'Other',
    'pr': 'Print',
    'tr': 'Transportation',
    'ev': 'Event',
    'ot': 'Other',
}

K_SOCIAL_MEDIA_FILTERS = {
    'fb': 'fb',
    'yt': 'yt',
    'ln': 'ln',
    'in': 'in',
    'x': 'x',
    'tt': 'tt',
    'wa': 'wa',
    'facebook': 'fb',
    'youTube': 'yt',
    'linkedIn': 'ln',
    'instagram': 'in',
    'tiktok': 'tt',
    'whatsapp': 'wa',
}

# Amazon S3
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
AWS_S3_FILE_OVERWRITE = False
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Other env variables
# GENERAL_AUTH_TOKEN = os.getenv('GENERAL_AUTH_TOKEN', None)
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'django_debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
