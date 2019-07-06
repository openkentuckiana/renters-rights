from __future__ import absolute_import

from .base import *

PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

MEDIA_URL = "/media/"
MEDIA_ROOT = "/tmp/"
