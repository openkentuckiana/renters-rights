import io
import logging
import sys
from concurrent.futures import FIRST_EXCEPTION, wait
from concurrent.futures.thread import ThreadPoolExecutor

import boto3
from django import forms
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.translation import gettext_lazy as _
from PIL import Image

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

    s3_documents = forms.CharField(widget=forms.HiddenInput(), required=False)

    s3_pictures = forms.CharField(widget=forms.HiddenInput(), required=False)

    def clean(self):
        if len(self.files.getlist("documents")) > settings.MAX_DOCUMENTS_PER_UNIT:
            raise forms.ValidationError(
                _("You may only upload a maximum of %(max_docs)d documents") % {"max_docs": settings.MAX_DOCUMENTS_PER_UNIT}
            )
        if len(self.files.getlist("pictures")) > settings.MAX_PICTURES_PER_UNIT:
            raise forms.ValidationError(
                _("You may only upload a maximum of %(max_pics)s pictures") % {"max_pics": settings.MAX_PICTURES_PER_UNIT}
            )

        if len(self.data.get("s3_documents", "").split(",")) > settings.MAX_DOCUMENTS_PER_UNIT:
            raise forms.ValidationError(
                _("You may only upload a maximum of %(max_docs)d documents") % {"max_docs": settings.MAX_DOCUMENTS_PER_UNIT}
            )
        if len(self.data.get("s3_pictures", []).split(",")) > settings.MAX_PICTURES_PER_UNIT:
            raise forms.ValidationError(
                _("You may only upload a maximum of %(max_pics)s pictures") % {"max_pics": settings.MAX_PICTURES_PER_UNIT}
            )

        return super().clean()

    def save(self, **kwargs):
        instance = super().save()

        def download_image(path):
            if not path:
                breakpoint()
                return None
            s3 = boto3.client(
                "s3", aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            s3_response_object = s3.get_object(Bucket=settings.AWS_UPLOAD_BUCKET_NAME, Key=path)
            thing = s3_response_object["Body"].read()

            # return ImageFile(ContentFile(thing))
            return InMemoryUploadedFile(ContentFile(thing), None, path, "image/png", len(thing), None)

        def create_image(img, image_type, owner, unit, download=False):
            if download:
                img = download_image(img)
            UnitImage.objects.create(image=img, image_type=image_type, owner=owner, unit=unit)

        documents = []
        pictures = []

        try:
            # Multithreading image creation can really speed up this request, but uses o(n) memory, which can be
            # problematic on Heroku
            with ThreadPoolExecutor(max_workers=settings.MAX_THREAD_POOL_WORKERS) as executor:
                futures = []
                for image in self.files.getlist("documents"):
                    futures.append(executor.submit(create_image, image, DOCUMENT, instance.owner, instance))
                for path in self.data.get("s3_documents", "").split(","):
                    futures.append(executor.submit(create_image, path, DOCUMENT, instance.owner, instance, True))
                for image in self.files.getlist("pictures"):
                    futures.append(executor.submit(create_image, image, PICTURE, instance.owner, instance))
                for path in self.data.get("s3_pictures", "").split(","):
                    futures.append(executor.submit(create_image, path, DOCUMENT, instance.owner, instance, True))
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
