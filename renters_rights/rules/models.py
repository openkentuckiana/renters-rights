import logging

from django.db import models
from django.utils.text import slugify

from lib.models import BaseModel

logger = logging.getLogger(__name__)


class Ordinance(BaseModel):
    ordinance = models.CharField(max_length=25)
    slug = models.SlugField(unique=True, max_length=50)
    title = models.CharField(max_length=255)
    legal_description = models.TextField()
    url = models.URLField()

    def __str__(self):
        return f"{self.ordinance} - {self.title}"


class RuleGroup(BaseModel):
    title = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, max_length=100)

    def __str__(self):
        return self.title


class Rule(BaseModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=50)
    ordinance = models.ManyToManyField(Ordinance)
    rule_group = models.ForeignKey(RuleGroup, on_delete=models.CASCADE)
    plain_description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.ordinance)
        super().save(*args, **kwargs)
