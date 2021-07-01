from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify

from lib.models import BaseModel

DEFAULT_CODE_LENGTH = 6
DEFAULT_CODE_TTL_MINUTES = 60


class User(AbstractUser, BaseModel):
    def __str__(self):
        return f"{self.username}"

    @property
    def slug(self):
        return slugify(self.username)
