"""Production settings and globals."""

from __future__ import absolute_import

import django_heroku

from .base import *

django_heroku.settings(locals())
DATABASES["default"]["ENGINE"] = "django.contrib.gis.db.backends.postgis"

DEBUG = str_to_bool(os.environ.get("DJANGO_DEBUG", False))

########## HOST CONFIGURATION
ALLOWED_HOSTS = get_env_variable("ALLOWED_HOSTS").split(",")
SECURE_SSL_REDIRECT = get_env_variable("SECURE_SSL_REDIRECT", True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
########## END HOST CONFIGURATION

########## EMAIL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-host
EMAIL_HOST = get_env_variable("EMAIL_HOST")

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-host-password
EMAIL_HOST_PASSWORD = get_env_variable("EMAIL_HOST_PASSWORD")

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-host-user
EMAIL_HOST_USER = get_env_variable("EMAIL_HOST_USER")

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-port
EMAIL_PORT = get_env_variable("EMAIL_PORT")

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
EMAIL_SUBJECT_PREFIX = "[%s] " % SITE_NAME

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-use-tls
EMAIL_USE_TLS = str_to_bool(get_env_variable("EMAIL_USE_TLS"))
EMAIL_USE_SSL = str_to_bool(get_env_variable("EMAIL_USE_SSL"))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#server-email
SERVER_EMAIL = EMAIL_HOST_USER
########## END EMAIL CONFIGURATION

########## CACHE CONFIGURATION
CACHES = {
    "default": {
        "BACKEND": "django_bmemcached.memcached.BMemcached",
        "LOCATION": os.environ.get("MEMCACHEDCLOUD_SERVERS").split(","),
        "TIMEOUT": CACHE_TIMEOUT,
        "OPTIONS": {
            "username": os.environ.get("MEMCACHEDCLOUD_USERNAME"),
            "password": os.environ.get("MEMCACHEDCLOUD_PASSWORD"),
        },
    }
}
########## END CACHE CONFIGURATION

########## SECRET CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = get_env_variable("SECRET_KEY")
########## END SECRET CONFIGURATION

########## STORAGE CONFIGURATION
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_DEFAULT_ACL = None
########## END STORAGE CONFIGURATION

if DEBUG:
    ########## TOOLBAR CONFIGURATION
    MIDDLEWARE += ("debug_toolbar.middleware.DebugToolbarMiddleware",)

    INSTALLED_APPS += ("debug_toolbar",)

    DEBUG_TOOLBAR_PATCH_SETTINGS = False

    # This should NEVER be used outside of debug mode, and should never be exposed to the public internet
    INTERNAL_IPS = type(str("c"), (), {"__contains__": lambda *a: True})()
    ########## END TOOLBAR CONFIGURATION
