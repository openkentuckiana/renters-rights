from django import forms
from django.forms import ModelChoiceField
from django.utils.translation import gettext_lazy as _
from localflavor.us.forms import USStateField, USZipCodeField
from phonenumber_field.formfields import PhoneNumberField

from documents.models import DocumentField
from units.models import Unit


# Heavily inspired by https://github.com/jessykate/django-survey
class DocumentForm(forms.Form):

    use_unit_address = forms.BooleanField(label=_("Use unit address?"), required=False)

    sender_address_1 = forms.CharField(label=_("Address 1"), max_length=100, required=False)
    sender_address_2 = forms.CharField(label=_("Address 2"), max_length=100, required=False)
    sender_city = forms.CharField(label=_("City"), max_length=100, required=False)
    sender_state = USStateField(label=_("State"), required=False)
    sender_zip_code = USZipCodeField(label=_("ZIP Code"), required=False)
    sender_email = forms.EmailField(label=_("Email Address"), required=False)
    sender_phone = PhoneNumberField(label=_("Phone Number"), required=False)

    def __init__(self, user, *args, **kwargs):
        # expects a survey object to be passed in initially
        document_template = kwargs.pop("document_template")
        self.document_template = document_template
        super().__init__(*args, **kwargs)

        self.fields["unit"] = ModelChoiceField(queryset=Unit.objects.for_user(user))

        data = kwargs.get("data")
        for f in document_template.document_fields.all():
            field_name = f.name.lower()

            if f.field_type == DocumentField.TEXT:
                self.fields[field_name] = forms.CharField(label=f.name)
            elif f.field_type == DocumentField.INTEGER:
                self.fields[field_name] = forms.IntegerField(label=f.name)
            elif f.field_type == DocumentField.DATE:
                self.fields[field_name] = forms.DateField(label=f.name)

            if f.required:
                self.fields[field_name].required = True
                self.fields[field_name].widget.attrs["class"] = "required"
            else:
                self.fields[field_name].required = False

            if data:
                self.fields[field_name].initial = data.get(field_name)

    @property
    def dynamic_fields(self):
        static_fields = (
            "unit",
            "use_unit_address",
            "sender_address_1",
            "sender_address_2",
            "sender_city",
            "sender_state",
            "sender_zip_code",
            "sender_email",
            "sender_phone",
        )
        return [v for (f, v) in self.fields.items() if f not in static_fields]
