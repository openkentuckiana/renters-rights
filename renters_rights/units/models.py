import datetime
import logging
import string
import sys
import uuid
from io import BytesIO
from random import choices

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.db.models import EmailField
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from localflavor.us.models import USStateField, USZipCodeField
from phonenumber_field.modelfields import PhoneNumberField
from PIL import Image

from lib.models import UserOwnedModel

logger = logging.getLogger(__name__)

DOCUMENT = "D"
MOVE_IN_PICTURE = "MIP"
MOVE_OUT_PICTURE = "MOP"


def generate_file_path(instance, filename):
    """Generates a file upload path.

    Args:
      instance: file instance.
      filename: name of the file.

    Returns: a path for uploading user images.
    """
    return f"uploads/{instance.owner.slug}/{filename}"


class Unit(UserOwnedModel):
    """Rental unit."""

    slug = models.SlugField(unique=True, max_length=60)

    # Location info
    unit_address_1 = models.CharField(_("Unit Address 1"), max_length=100)
    unit_address_2 = models.CharField(_("Unit Address 2"), max_length=100, blank=True)
    unit_city = models.CharField(_("Unit City"), max_length=100, blank=True)
    unit_state = USStateField(_("Unit State"))
    unit_zip_code = USZipCodeField(_("Unit ZIP Code"))

    # Landlord info
    landlord_name = models.CharField(_("Landlord Name"), max_length=100, blank=True)
    landlord_address_1 = models.CharField(_("Landlord Address 1"), max_length=100, blank=True)
    landlord_address_2 = models.CharField(_("Landlord Address 2"), max_length=100, blank=True)
    landlord_city = models.CharField(_("Landlord City"), max_length=100, blank=True)
    landlord_state = USStateField(_("Landlord State"), blank=True)
    landlord_zip_code = USZipCodeField(_("Landlord ZIP Code"), blank=True)
    landlord_phone_number = PhoneNumberField(_("Landlord Phone Number"), blank=True)
    landlord_email = EmailField(_("Landlord Email"), blank=True)

    # Lease info
    lease_start_date = models.DateField(_("Lease Start Start Date"), blank=True, null=True)
    lease_end_date = models.DateField(_("Lease Start End Date"), blank=True, null=True)
    rent_due_date = models.PositiveIntegerField(_("Day Rent Due"), blank=True, null=True)

    def __str__(self):
        return f"{self.unit_address_1}"

    def get_absolute_url(self):
        return reverse("unit-detail", args=[self.slug])

    def pictures(self):
        return self.unitimage_set.filter(image_type__in=(MOVE_IN_PICTURE, MOVE_OUT_PICTURE)).order_by("-created_at")

    def move_in_pictures(self):
        return self.unitimage_set.filter(image_type=MOVE_IN_PICTURE).order_by("-created_at")

    def move_out_pictures(self):
        return self.unitimage_set.filter(image_type=MOVE_OUT_PICTURE).order_by("-created_at")

    def documents(self):
        return self.unitimage_set.filter(image_type=DOCUMENT).order_by("-created_at")

    def has_landlord_into(self):
        return (
            self.landlord_name
            or self.landlord_address_1
            or self.landlord_address_2
            or self.landlord_city
            or self.landlord_state
            or self.landlord_zip_code
            or self.landlord_phone_number
            or self.landlord_email
        )

    def has_lease_info(self):
        return self.lease_start_date or self.lease_end_date or self.rent_due_date

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{slugify(self.unit_address_1)[:45]}-{''.join(choices(string.ascii_lowercase + string.digits, k=10))}"
        super().save(*args, **kwargs)


class UnitImage(UserOwnedModel):
    IMAGE_TYPE_CHOICES = [(DOCUMENT, "Document"), (MOVE_IN_PICTURE, "Move In Picture"), (MOVE_OUT_PICTURE, "Move Out Picture")]

    image = models.ImageField(upload_to=generate_file_path)
    full_size_height = models.PositiveIntegerField(default=0)
    full_size_width = models.PositiveIntegerField(default=0)
    thumbnail_sizes = ArrayField(models.SmallIntegerField(), blank=True, null=True)
    image_type = models.CharField(max_length=3, choices=IMAGE_TYPE_CHOICES, default=DOCUMENT)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)

    @property
    def thumbnail(self):
        cache_key = f"image-{self.id}"
        thumb = cache.get(cache_key)
        if not thumb:
            thumb = default_storage.url(f"{self.image.name.split('.')[0]}-{self.thumbnail_sizes[-1]}.jpg")
            cache.add(cache_key, thumb)
        return thumb

    @property
    def thumbnail_internal(self):
        """Gets a thumbnail that can accessed from the application server.

        Returns: A thumbnail URL that can be accessed from the application server.
        """
        return default_storage.url(f"{self.image.name.split('.')[0]}-{self.thumbnail_sizes[0]}.jpg").replace("localhost", "s3")

    def __str__(self):
        return f"{self.image.name}"

    def upload_time(self):
        return f"{self.created_at.strftime('%A %B %m, %Y at %I:%M %p')} GMT"

    def save(self, *args, **kwargs):
        min_size = settings.UNIT_IMAGE_MIN_HEIGHT_AND_WIDTH
        max_size = settings.UNIT_IMAGE_MAX_HEIGHT_AND_WIDTH
        if self.image.height < min_size or self.image.width < min_size:
            raise ValidationError(_(f"Images must be over {min_size} pixels tall and wide. Please upload a larger image."))

        file_path = f"uploads/{self.owner.slug}/{str(uuid.uuid4())}"
        self.thumbnail_sizes = []

        im = Image.open(self.image).convert("RGB")
        original_width, original_height = im.size

        # Process images from larges to smallest so we can continually resize the same image.
        sizes = settings.UNIT_IMAGE_SIZES
        sizes.sort(reverse=True)
        for size in sizes:
            output = BytesIO()
            if original_width > size or original_height > size:
                factor = max(size / original_width, size / original_height)
                im = im.resize((round(original_width * factor), round(original_height * factor)), Image.LANCZOS)

            # if this is the smallest size, make a square thumbnail.
            if size == min_size:
                im = im.crop((0, 0, size, size))

            im.save(output, format="JPEG", quality=75)

            output.seek(0)

            if size != max_size:
                default_storage.save(f"{file_path}-{size}.jpg", ContentFile(output.read()))
                self.thumbnail_sizes.append(size)
            else:
                self.full_size_width = im.size[0]
                self.full_size_height = im.size[1]

                self.image = InMemoryUploadedFile(
                    output, "ImageField", f"{file_path}.jpg", "image/jpeg", sys.getsizeof(output), None
                )

        self.unit.modified_at = datetime.datetime.utcnow()
        self.unit.save()
        super().save(*args, **kwargs)


@receiver(post_delete, sender=UnitImage)
def delete_thumbnails(sender, instance, using, **kwargs):
    """Post-delete signal handler to delete thumbnail images."""
    default_storage.delete(instance.image.name)

    for size in instance.thumbnail_sizes:
        default_storage.delete(f"{instance.image.name.split('.')[0]}-{size}.jpg")
