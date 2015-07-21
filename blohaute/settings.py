"""
Django settings for blohaute project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
# import environ
# root = environ.Path(__file__) - 2  # three folder back (/a/b/c/ - 3 = /)
# print root
# env = environ.Env(DEBUG=(bool, False),)  # set default values and casting
# environ.Env.read_env('.myenv')  # reading .env file
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '9$1d0$45+y)#%26isbxl89at@5e30vqlg8)vg#&s0k+5^o)=r%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR, 'templates').replace('\\', '/'),
)

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)

ALLOWED_HOSTS = ['www.blohaute.com', 'blohaute.com', 'beta.blohaute.com']


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # 3rd party libraries
    'widget_tweaks',  # allows easy modification of form widgets
    'changuito',  # shopping cart
    'django_bleach',  # safe html sanitizing
    'django_extensions',
    'localflavor',
    'adminsortable',
    'raven.contrib.django.raven_compat',
    'rest_framework',
    'rest_framework.authtoken',
    # project apps
    'accounts',
    'booking',
    'settings',

    # blog
    'taggit',
    'blog',
    'markdown_deux',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'changuito.middleware.CartMiddleware',
    'booking.middleware.BookerMiddleware',
    #'raven.contrib.django.raven_compat.middleware.Sentry404CatchMiddleware',

)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

ROOT_URLCONF = 'blohaute.urls'

WSGI_APPLICATION = 'blohaute.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    #'default': env.db(),  # Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
}

AUTH_USER_MODEL = 'accounts.User'

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, "media")


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        #'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    )
}


BLOHAUTE_LOCATION_ID = '29033'

LOGIN_URL = '/account/login/'
try:
    from local_settings import *
except ImportError:
    pass