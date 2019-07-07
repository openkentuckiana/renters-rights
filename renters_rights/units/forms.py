import logging

from django import forms
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from units.models import DOCUMENT, PICTURE, Unit, UnitImage, delete_thumbnails

logger = logging.getLogger(__name__)


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = [
            "unit_address_1",
            "unit_address_2",
            "unit_city",
            "unit_state",
            "unit_zip_code",
            "landlord_address_1",
            "landlord_address_2",
            "landlord_city",
            "landlord_state",
            "landlord_zip_code",
            "landlord_phone_number",
            "lease_start_date",
            "lease_end_date",
            "rent_due_date",
        ]

    documents = forms.ImageField(
        label=_("Documents"),
        widget=forms.ClearableFileInput(attrs={"multiple": True}),
        required=False,
    )

    pictures = forms.ImageField(
        label=_("Pictures"),
        widget=forms.ClearableFileInput(attrs={"multiple": True}),
        required=False,
    )

    @transaction.atomic
    def save(self):
        instance = super().save()

        documents = []
        pictures = []

        try:
            for file in self.files.getlist("documents"):
                documents.append(
                    UnitImage.objects.create(
                        image=file,
                        image_type=DOCUMENT,
                        owner=instance.owner,
                        unit=instance,
                    )
                )
            for file in self.files.getlist("pictures"):
                pictures.append(
                    UnitImage.objects.create(
                        image=file,
                        image_type=PICTURE,
                        owner=instance.owner,
                        unit=instance,
                    )
                )
        except Exception:
            logger.debug(
                "Failed to create unit or unit images. Deleting any uploaded images and thumbnails."
            )
            for i in documents + pictures:
                delete_thumbnails(None, i, None)
            raise

        return instance
