from django import forms
from django.forms import ModelChoiceField
from django.utils.translation import gettext_lazy as _
from localflavor.us.forms import USStateField, USStateSelect, USZipCodeField
from phonenumber_field.formfields import PhoneNumberField

from documents.models import DocumentField
from units.models import Unit


# Heavily inspired by https://github.com/jessykate/django-survey
class BaseDocumentForm(forms.Form):
    use_unit_address = forms.BooleanField(label=_("Use unit address?"), required=False)

    sender_address_1 = forms.CharField(label=_("Address 1"), max_length=100, required=False)
    sender_address_2 = forms.CharField(label=_("Address 2"), max_length=100, required=False)
    sender_city = forms.CharField(label=_("City"), max_length=100, required=False)
    sender_state = USStateField(label=_("State"), required=False, widget=USStateSelect)
    sender_zip_code = USZipCodeField(label=_("ZIP Code"), required=False)
    sender_email = forms.EmailField(label=_("Email Address"), required=False)
    sender_phone = PhoneNumberField(label=_("Phone Number"), required=False)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not user.first_name and not user.last_name:
            self.fields["sender_first_name"] = forms.CharField(label=_("Your First Name"))
            self.fields["sender_last_name"] = forms.CharField(label=_("Your Last Name"))

        self.fields["unit"] = ModelChoiceField(queryset=Unit.objects.for_user(user))

    @property
    def name_fields(self):
        static_fields = ("sender_first_name", "sender_last_name")
        return [v for (f, v) in self.fields.items() if f in static_fields]

    @property
    def additional_fields(self):
        """Gets fields that are defined in addition to the base fields. Either by a subclass or a document template..

        Returns: A list of fields that have been added to the form's set of base fields.

        """
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
            "sender_first_name",
            "sender_last_name",
        )
        return [self.__getitem__(f) for (f, v) in self.fields.items() if f not in static_fields]

    def clean(self):
        super().clean()
        use_unit_address = self.cleaned_data.get("use_unit_address")
        sender_address_1 = self.cleaned_data.get("sender_address_1")
        sender_city = self.cleaned_data.get("sender_city")
        sender_state = self.cleaned_data.get("sender_state")
        sender_zip_code = self.cleaned_data.get("sender_zip_code")

        if not use_unit_address and (not sender_address_1 or not sender_city or not sender_state or not sender_zip_code):
            raise forms.ValidationError({"sender_address_1": _("Please enter your contact information.")})
        elif use_unit_address:
            if not self.cleaned_data.get("unit"):
                return  # error will be raised by unit field clean method
            self.cleaned_data["sender_address_1"] = self.cleaned_data["unit"].unit_address_1
            self.cleaned_data["sender_address_2"] = self.cleaned_data["unit"].unit_address_2
            self.cleaned_data["sender_city"] = self.cleaned_data["unit"].unit_city
            self.cleaned_data["sender_state"] = self.cleaned_data["unit"].unit_state
            self.cleaned_data["sender_zip_code"] = self.cleaned_data["unit"].unit_zip_code


class DocumentForm(BaseDocumentForm):
    def __init__(self, user, *args, **kwargs):
        # expects a survey object to be passed in initially
        document_template = kwargs.pop("document_template")
        self.document_template = document_template
        super().__init__(user, *args, **kwargs)

        for f in document_template.document_fields.all():
            field_name = f.name.lower()

            if f.field_type == DocumentField.TEXT:
                self.fields[field_name] = forms.CharField(label=f.name, required=f.required)
            elif f.field_type == DocumentField.INTEGER:
                self.fields[field_name] = forms.IntegerField(label=f.name, required=f.required)
            elif f.field_type == DocumentField.DATE:
                self.fields[field_name] = forms.DateField(label=f.name, required=f.required)

            if f.required:
                self.fields[field_name].required = True
                self.fields[field_name].widget.attrs["class"] = "required"
            else:
                self.fields[field_name].required = False


class PhotosDocumentForm(BaseDocumentForm):
    pass


class SmallClaimsDocumentForm(BaseDocumentForm):
    kentucky_counties = (
        (c, c)
        for c in (
            "Adair",
            "Allen",
            "Anderson",
            "Ballard",
            "Barren",
            "Bath",
            "Bell",
            "Boone",
            "Bourbon",
            "Boyd",
            "Boyle",
            "Bracken",
            "Breathitt",
            "Breckinridge",
            "Bullitt",
            "Butler",
            "Caldwell",
            "Calloway",
            "Campbell",
            "Carlisle",
            "Carroll",
            "Carter",
            "Casey",
            "Christian",
            "Clark",
            "Clay",
            "Clinton",
            "Crittenden",
            "Cumberland",
            "Daviess",
            "Edmonson",
            "Elliott",
            "Estill",
            "Fayette",
            "Fleming",
            "Floyd",
            "Franklin",
            "Fulton",
            "Gallatin",
            "Garrard",
            "Grant",
            "Graves",
            "Grayson",
            "Green",
            "Greenup",
            "Hancock",
            "Hardin",
            "Harlan",
            "Harrison",
            "Hart",
            "Henderson",
            "Henry",
            "Hickman",
            "Hopkins",
            "Jackson",
            "Jefferson",
            "Jessamine",
            "Johnson",
            "Kenton",
            "Knott",
            "Knox",
            "Larue",
            "Laurel",
            "Lawrence",
            "Lee",
            "Leslie",
            "Letcher",
            "Lewis",
            "Lincoln",
            "Livingston",
            "Logan",
            "Lyon",
            "McCracken",
            "McCreary",
            "McLean",
            "Madison",
            "Magoffin",
            "Marion",
            "Marshall",
            "Martin",
            "Mason",
            "Meade",
            "Menifee",
            "Mercer",
            "Metcalfe",
            "Monroe",
            "Montgomery",
            "Morgan",
            "Muhlenberg",
            "Nelson",
            "Nicholas",
            "Ohio",
            "Oldham",
            "Owen",
            "Owsley",
            "Pendleton",
            "Perry",
            "Pike",
            "Powell",
            "Pulaski",
            "Robertson",
            "Rockcastle",
            "Rowan",
            "Russell",
            "Scott",
            "Shelby",
            "Simpson",
            "Spencer",
            "Taylor",
            "Todd",
            "Trigg",
            "Trimble",
            "Union",
            "Warren",
            "Washington",
            "Wayne",
            "Webster",
            "Whitley",
            "Wolfe",
            "Woodford",
        )
    )

    county = forms.ChoiceField(label=_("County where you are filing"), choices=kentucky_counties)
    is_landlord_company = forms.BooleanField(label=_("Is your landlord a company?"), required=False)
    claims_sum = forms.DecimalField(label=_("How much are you asking for?"), decimal_places=2, min_value=0, max_value=2500)
    court_costs = forms.DecimalField(label=_("How much do you think court costs are (ex $50)?"), decimal_places=2, min_value=0)
    claims = forms.CharField(label=_("Your claims against your landlord"), widget=forms.Textarea)
