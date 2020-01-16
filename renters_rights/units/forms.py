import logging

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from localflavor.us.us_states import CONTIGUOUS_STATES

from units.models import Unit

logger = logging.getLogger(__name__)


class UnitForm(forms.ModelForm):
    error_css_class = "error"
    required_css_class = "required"

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

    @staticmethod
    def _get_state_name(state_code):
        try:
            return next(s for s in CONTIGUOUS_STATES if s[0] == state_code)[1]
        except Exception:
            return None

    def clean(self):
        cleaned_data = super().clean()
        state = cleaned_data.get("unit_state")
        state_name = self._get_state_name(state)
        zip_code = cleaned_data.get("unit_zip_code")

        if not state or not zip_code:
            return  # unit_state nad unit_zip_code being required fields will result in a required message if this isn't set

        if self._get_state_name(state) not in settings.SUPPORTED_JURISDICTION_STATES:
            raise forms.ValidationError({"unit_state": _("Sorry, but we do not support that state at this time")})

        if "ALL" in settings.SUPPORTED_JURISDICTIONS[state_name]:
            return

        if zip_code not in settings.SUPPORTED_JURISDICTION_ZIP_CODES_BY_STATE[state_name]:
            raise forms.ValidationError(
                _(
                    "Sorry, but we only support jurisdictions that have adopted the Uniform Residential Landlord Tenant Act. In %(state)s, those jurisdictions are: %(jurisdictions)s"
                    % {"state": state_name, "jurisdictions": ", ".join(settings.SUPPORTED_JURISDICTIONS[state_name].keys())}
                )
            )


class UnitAddImageForm(forms.Form):
    error_css_class = "error"
    required_css_class = "required"

    def __init__(
        self,
        unit,
        label,
        max_images,
        current_image_count,
        upload_instructions,
        upload_ideas,
        upload_instructions_footer=None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.unit = unit
        self.label = label
        self.max_images = max_images
        self.current_image_count = current_image_count
        self.upload_instructions = upload_instructions
        self.upload_ideas = upload_ideas
        self.upload_instructions_footer = upload_instructions_footer

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
