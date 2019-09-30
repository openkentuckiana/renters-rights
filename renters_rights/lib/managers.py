from django.db import models
from django.shortcuts import get_object_or_404


class UserOwnedModelManager(models.Manager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def for_user(self, user, **kwargs):
        return self.get_queryset().filter(owner=user, **kwargs)

    def get_for_user(self, user, **kwargs):
        return get_object_or_404(self.get_queryset(), owner=user, **kwargs)
