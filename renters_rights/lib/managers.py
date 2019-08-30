from django.db import models


class UserOwnedModelManager(models.Manager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def for_user(self, user, **kwargs):
        return self.get_queryset().filter(owner=user, **kwargs)

    def get_for_user(self, user, **kwargs):
        return self.get_queryset().get(owner=user, **kwargs)
