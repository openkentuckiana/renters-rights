import logging
from concurrent.futures import FIRST_EXCEPTION, wait
from concurrent.futures.thread import ThreadPoolExecutor

from django import forms
from django.conf import settings
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
        label=_("Documents"), widget=forms.ClearableFileInput(attrs={"multiple": True}), required=False
    )

    pictures = forms.ImageField(label=_("Pictures"), widget=forms.ClearableFileInput(attrs={"multiple": True}), required=False)

    def clean(self):
        if len(self.files.getlist("documents")) > settings.MAX_DOCUMENTS_PER_UNIT:
            raise forms.ValidationError(
                _("You may only upload a maximum of %(max_docs)d documents") % {"max_docs": settings.MAX_DOCUMENTS_PER_UNIT}
            )
        if len(self.files.getlist("pictures")) > settings.MAX_PICTURES_PER_UNIT:
            raise forms.ValidationError(
                _("You may only upload a maximum of %(max_pics)s pictures") % {"max_pics": settings.MAX_PICTURES_PER_UNIT}
            )

    def save(self, **kwargs):
        instance = super().save()

        def create_image(file, image_type, owner, unit):
            UnitImage.objects.create(image=file, image_type=image_type, owner=owner, unit=unit)

        documents = []
        pictures = []

        try:
            with ThreadPoolExecutor() as executor:
                futures = []
                for file in self.files.getlist("documents"):
                    futures.append(executor.submit(create_image, file, DOCUMENT, instance.owner, instance))
                for file in self.files.getlist("pictures"):
                    futures.append(executor.submit(create_image, file, PICTURE, instance.owner, instance))
                wait(futures, return_when=FIRST_EXCEPTION)
                for f in futures:
                    if f.exception():
                        raise f.exception()
        except Exception:
            logger.debug("Failed to create unit or unit images. Deleting any uploaded images and thumbnails.")
            for i in documents + pictures:
                delete_thumbnails(None, i, None)
            try:
                instance.delete()
            except Exception:
                logger.exception("Failed to delete Unit")
            raise

        return instance
