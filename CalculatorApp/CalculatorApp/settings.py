import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['0.0.0.0', 'localhost']

# Application definition
EXE_PATH = BASE_DIR.parent/"build"/"app.exe"
MAKE_PATH = BASE_DIR.parent/"Makefile"
SYNC_PERIOD = 10 # seconds

INSTALLED_APPS = [
    'daphne',
    'rest_framework',
    'main_app',
]

MIDDLEWARE = []

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get('REDIS_URL', 'redis://localhost:6379')],
        },
    },
}

ROOT_URLCONF = 'CalculatorApp.urls'

WSGI_APPLICATION = 'CalculatorApp.wsgi.application'
ASGI_APPLICATION = 'CalculatorApp.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = False

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standart': {
            'format': '{levelname:8} [{asctime}] {name}: {message}',
            'style': '{'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'formatter': 'standart',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'DEBUG',
            'formatter': 'standart',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR/'calc-server.log',
        }
    },
    'loggers': {
        'daphne': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'django.channels': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False
        },
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True
        },
        'django.db.backends': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
    },
}