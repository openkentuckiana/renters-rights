from django.db import models


class UserOwnedModelManager(models.Manager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def for_user(self, user):
        return self.get_queryset().filter(owner=user)
