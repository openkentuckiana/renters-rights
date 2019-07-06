import datetime
import string
import sys
import uuid
from io import BytesIO
from random import choices

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from PIL import Image

from lib.models import BaseModel, SoftDeleteModel









def generate_file_path(instance, filename):
    """Generates a file upload path."""
    return f'uploads/{datetime.datetime.utcnow().strftime("%Y/%m/%d")}/{filename}'


class UnitImage(BaseModel):
    image = models.ImageField(upload_to=generate_file_path)
    item = models.ForeignKey("Item", on_delete=models.CASCADE)
    full_size_height = models.PositiveIntegerField(default=0)
    full_size_width = models.PositiveIntegerField(default=0)
    thumbnail_sizes = ArrayField(models.SmallIntegerField(), blank=True, null=True)

    def __str__(self):
        return f"{self.image.name} - {self.item.name}"

    def save(self, *args, **kwargs):
        min_size = settings.UNIT_IMAGE_MIN_HEIGHT_AND_WIDTH
        if self.image.height < min_size or self.image.width < min_size:
            raise ValidationError(
                _(
                    f"Images must be over {min_size} pixels tall and wide. Please upload a larger image."
                )
            )

        file_path = f'uploads/{datetime.datetime.utcnow().strftime("%Y/%m/%d")}/{str(uuid.uuid4())}'
        self.thumbnail_sizes = []

        settings.UNIT_IMAGE_SIZES.sort()
        for size in settings.UNIT_IMAGE_SIZES:
            output = BytesIO()

            im = Image.open(self.image).convert("RGB")
            original_width, original_height = im.size
            if original_width > size or original_height > size:
                factor = max(size / original_width, size / original_height)
                im = im.resize(
                    (round(original_width * factor), round(original_height * factor))
                )

            # if this is the smallest size, make a square thumbnail.
            if size == settings.UNIT_IMAGE_SIZES[0]:
                im = im.crop((0, 0, size, size))

            im.save(output, format="JPEG", quality=100)

            output.seek(0)

            if size != settings.UNIT_IMAGE_SIZES[-1]:
                default_storage.save(
                    f"{file_path}-{size}.jpg", ContentFile(output.read())
                )
                self.thumbnail_sizes.append(size)
            else:
                self.full_size_width = im.size[0]
                self.full_size_height = im.size[1]

                self.image = InMemoryUploadedFile(
                    output,
                    "ImageField",
                    f"{file_path}.jpg",
                    "image/jpeg",
                    sys.getsizeof(output),
                    None,
                )

        super().save(*args, **kwargs)


@receiver(post_delete, sender=UnitImage)
def delete_thumbnails(sender, instance, using, **kwargs):
    """Post-delete signal handler to delete thumbnail images."""
    default_storage.delete(instance.image.path)

    for size in instance.thumbnail_sizes:
        default_storage.delete(f"{instance.image.path.split('.')[0]}-{size}.jpg")


class Item(SoftDeleteModel):
    """
    Items that users are willing to give up.
    """

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=60)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey("noauth.User", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        self.slug = f"{slugify(self.name)[:45]}-{''.join(choices(string.ascii_lowercase + string.digits, k=10))}"
        super().save(*args, **kwargs)
