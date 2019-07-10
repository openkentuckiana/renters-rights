import datetime
import logging
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
from localflavor.us.models import USStateField, USZipCodeField
from phonenumber_field.modelfields import PhoneNumberField
from PIL import Image

from lib.models import UserOwnedModel

logger = logging.getLogger(__name__)

DOCUMENT = "D"
PICTURE = "P"


def generate_file_path(instance, filename):
    """Generates a file upload path."""
    return f'uploads/{datetime.datetime.utcnow().strftime("%Y/%m/%d")}/{filename}'


class Unit(UserOwnedModel):
    """
    Items that users are willing to give up.
    """

    slug = models.SlugField(unique=True, max_length=60)

    # Location info
    unit_address_1 = models.CharField(_("Unit Address 1"), max_length=100)
    unit_address_2 = models.CharField(_("Unit Address 2"), max_length=100, blank=True)
    unit_city = models.CharField(_("Unit City"), max_length=100, blank=True)
    unit_state = USStateField(_("Unit State"), blank=True)
    unit_zip_code = USZipCodeField(_("Unit ZIP Code"), blank=True)

    # Landlord info
    landlord_address_1 = models.CharField(_("Landlord Address 1"), max_length=100, blank=True)
    landlord_address_2 = models.CharField(_("Landlord Address 2"), max_length=100, blank=True)
    landlord_city = models.CharField(_("Landlord City"), max_length=100, blank=True)
    landlord_state = USStateField(_("Landlord State"), blank=True)
    landlord_zip_code = USZipCodeField(_("Landlord ZIP Code"), blank=True)
    landlord_phone_number = PhoneNumberField(_("Landlord Phone Number"), blank=True)

    # Lease info
    lease_start_date = models.DateField(_("Lease Start Start Date"), blank=True, null=True)
    lease_end_date = models.DateField(_("Lease Start End Date"), blank=True, null=True)
    rent_due_date = models.PositiveIntegerField(_("Day Rent Date"), blank=True, null=True)

    def __str__(self):
        return f"{self.unit_address_1}"

    def save(self, *args, **kwargs):
        self.slug = f"{slugify(self.unit_address_1)[:45]}-{''.join(choices(string.ascii_lowercase + string.digits, k=10))}"
        super().save(*args, **kwargs)


class UnitImage(UserOwnedModel):
    IMAGE_TYPE_CHOICES = [(DOCUMENT, "Document"), (PICTURE, "Picture")]

    image = models.ImageField(upload_to=generate_file_path)
    full_size_height = models.PositiveIntegerField(default=0)
    full_size_width = models.PositiveIntegerField(default=0)
    thumbnail_sizes = ArrayField(models.SmallIntegerField(), blank=True, null=True)
    image_type = models.CharField(max_length=1, choices=IMAGE_TYPE_CHOICES, default=PICTURE)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.image.name}"

    def save(self, *args, **kwargs):
        min_size = settings.UNIT_IMAGE_MIN_HEIGHT_AND_WIDTH
        if self.image.height < min_size or self.image.width < min_size:
            raise ValidationError(_(f"Images must be over {min_size} pixels tall and wide. Please upload a larger image."))

        file_path = f'uploads/{datetime.datetime.utcnow().strftime("%Y/%m/%d")}/{str(uuid.uuid4())}'
        self.thumbnail_sizes = []

        settings.UNIT_IMAGE_SIZES.sort()
        im_original = Image.open(self.image).convert("RGB")
        original_width, original_height = im_original.size

        for size in settings.UNIT_IMAGE_SIZES:
            im = im_original.copy()
            output = BytesIO()

            if original_width > size or original_height > size:
                factor = max(size / original_width, size / original_height)
                im = im.resize((round(original_width * factor), round(original_height * factor)), Image.LANCZOS)

            # if this is the smallest size, make a square thumbnail.
            if size == settings.UNIT_IMAGE_SIZES[0]:
                im = im.crop((0, 0, size, size))

            im.save(output, format="JPEG", quality=75)

            output.seek(0)

            if size != settings.UNIT_IMAGE_SIZES[-1]:
                default_storage.save(f"{file_path}-{size}.jpg", ContentFile(output.read()))
                self.thumbnail_sizes.append(size)
            else:
                self.full_size_width = im.size[0]
                self.full_size_height = im.size[1]

                self.image = InMemoryUploadedFile(
                    output, "ImageField", f"{file_path}.jpg", "image/jpeg", sys.getsizeof(output), None
                )

        super().save(*args, **kwargs)


@receiver(post_delete, sender=UnitImage)
def delete_thumbnails(sender, instance, using, **kwargs):
    """Post-delete signal handler to delete thumbnail images."""
    try:
        try:
            default_storage.delete(instance.image.name)

            for size in instance.thumbnail_sizes:
                default_storage.delete(f"{instance.image.name.split('.')[0]}-{size}.jpg")
        except Exception:
            # Local dev, use full path
            default_storage.delete(instance.image.path)

            for size in instance.thumbnail_sizes:
                default_storage.delete(f"{instance.image.path.split('.')[0]}-{size}.jpg")
    except Exception:
        logger.exception("Could not delete image(s) %s", instance.image.path)
