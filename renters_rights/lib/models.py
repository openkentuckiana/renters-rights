from django.db import models

from lib.managers import UserOwnedModelManager


class BaseModel(models.Model):
    objects = UserOwnedModelManager()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserOwnedModel(BaseModel):
    owner = models.ForeignKey("noauth.User", on_delete=models.CASCADE)

    class Meta:
        abstract = True
