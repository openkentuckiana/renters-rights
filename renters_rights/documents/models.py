from django.db import models
from django.db.models import CASCADE


class DocumentTemplate(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50)
    body = models.TextField(
        help_text="Template to be rendered using Django template engine. The template will receive a User object named user, "
        "a Unit object named unit, and any fields that are related to this template."
    )

    def fields(self):
        if self.pk:
            return DocumentField.objects.filter(document=self.pk)
        else:
            return None

    def __str__(self):
        return self.name


class DocumentField(models.Model):
    DATE = "date"
    INTEGER = "integer"
    TEXT = "text"

    FIELD_TYPES = ((DATE, "date"), (INTEGER, "integer"), (TEXT, "text"))

    name = models.CharField(max_length=50)
    required = models.BooleanField()
    field_type = models.CharField(max_length=10, choices=FIELD_TYPES, default=TEXT)
    document = models.ForeignKey(DocumentTemplate, on_delete=CASCADE, related_name="document_fields")

    class Meta:
        unique_together = ("name", "document")

    def __str__(self):
        return self.name
