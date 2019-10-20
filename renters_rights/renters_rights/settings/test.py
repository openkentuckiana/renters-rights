from __future__ import absolute_import

from .base import *

PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

MEDIA_URL = "/media/"
MEDIA_ROOT = "/tmp/"

STATICFILES_STORAGE = None

SUPPORTED_JURISDICTIONS = {"Kentucky": {"Barbourville": [40906]}, "Indiana": {"ALL": []}}

# next three variables shouldn't need to change even if SUPPORTED_JURISDICTIONS changes
SUPPORTED_JURISDICTION_STATES = {s for s in SUPPORTED_JURISDICTIONS.keys()}
SUPPORTED_JURISDICTION_NAMES_BY_STATE = {
    state: list(jurisdictions.keys()) for state, jurisdictions in SUPPORTED_JURISDICTIONS.items()
}
SUPPORTED_JURISDICTION_ZIP_CODES_BY_STATE = {
    state: [str(z) for z in [zip_list for j in list(jurisdictions.values()) for zip_list in j]]
    for state, jurisdictions in SUPPORTED_JURISDICTIONS.items()
}
