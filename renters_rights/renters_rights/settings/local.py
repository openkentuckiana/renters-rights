"""Development settings and globals."""

from .base import *

########## DEBUG CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
TEMPLATE_DEBUG = DEBUG
########## END DEBUG CONFIGURATION

########## EMAIL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
########## END EMAIL CONFIGURATION

########## TOOLBAR CONFIGURATION
MIDDLEWARE += ("debug_toolbar.middleware.DebugToolbarMiddleware",)

INSTALLED_APPS += ("debug_toolbar",)

DEBUG_TOOLBAR_PATCH_SETTINGS = False

# This should NEVER be used outside of local.py
INTERNAL_IPS = type(str("c"), (), {"__contains__": lambda *a: True})()
########## END TOOLBAR CONFIGURATION

NOAUTH_ALLOWED_EMAILS = ["test@example.com"]

MEDIA_URL = "/media/"
MEDIA_ROOT = "/tmp/"
