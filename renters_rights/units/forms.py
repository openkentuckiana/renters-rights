import logging

from django import forms
from django.utils.translation import gettext_lazy as _

from units.models import Unit

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
            "landlord_name",
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


class UnitAddImageForm(forms.Form):
    def __init__(self, unit, label, max_images, current_image_count, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unit = unit
        self.label = label
        self.max_images = max_images
        self.current_image_count = current_image_count

        self.fields["images"] = forms.ImageField(
            label=self.label, widget=forms.ClearableFileInput(attrs={"multiple": True}), required=False
        )

    s3_images = forms.CharField(widget=forms.HiddenInput(), required=False)

    def clean(self):
        s3_images = [i for i in self.data.get("s3_images", "").split(",") if i]
        if not (self.files and len(self.files.getlist("images")) > 0) and not len(s3_images) > 0:
            raise forms.ValidationError(_("Please select at least one image."))

        error_message = _("You may only upload a maximum of %(max_docs)d %(item_name)s.") % {
            "max_docs": self.max_images,
            "item_name": self.label.lower(),
        }

        if self.current_image_count > 0:
            error_message = _(
                "You may only upload a maximum of %(max_docs)d %(item_name)s. You already have %(current_image_count)d."
            ) % {"max_docs": self.max_images, "item_name": self.label.lower(), "current_image_count": self.current_image_count}

        if self.files and (len(self.files.getlist("images")) + self.current_image_count) > self.max_images:
            raise forms.ValidationError(error_message)

        if (len(s3_images) + self.current_image_count) > self.max_images:
            raise forms.ValidationError(error_message)

        return super().clean()
