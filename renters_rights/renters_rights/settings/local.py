"""Development settings and globals."""
import time

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

MEDIA_URL = "/media/"
MEDIA_ROOT = "/tmp/"


BASE_DIR = os.path.dirname(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)))))
STATICFILES_DIRS = [os.path.join(BASE_DIR, "public")]

########## S3 CONFIGURATION
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

AWS_S3_ENDPOINT_URL = "http://s3:4566"  # Used by boto to connect from app container to s3 container
AWS_S3_CUSTOM_DOMAIN = f"localhost:4566/{AWS_STORAGE_BUCKET_NAME}"  # used by django-storages to generate URLs for frontend
AWS_S3_SECURE_URLS = False  # Localstack s3 does not support SSL

sleep = 1
while sleep < 30:
    import boto3

    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            endpoint_url=AWS_S3_ENDPOINT_URL,
        )
        s3.create_bucket(Bucket=AWS_UPLOAD_BUCKET_NAME)
        s3.create_bucket(Bucket=AWS_STORAGE_BUCKET_NAME)
        break
    except:
        print(f"Couldn't connect to mock s3. Sleeping {sleep} before trying again.")
        time.sleep(sleep)
        sleep *= 2
########## END S3 CONFIGURATION
