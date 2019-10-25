from django import forms
from django.utils.translation import gettext_lazy as _


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email address", max_length=100)


class CodeForm(forms.Form):
    email = forms.EmailField(label="Email address", max_length=100)
    code = forms.CharField(label="Code", max_length=20)


class UserProfileForm(forms.Form):
    first_name = forms.CharField(label=_("First name"), max_length=100, required=True)
    last_name = forms.CharField(label=_("Last name"), max_length=100, required=True)
    email = forms.CharField(
        label=_("Email"), help_text=_("If you change this, you will need to log in using your new address"), required=False
    )
    confirm_email = forms.CharField(label=_("Confirm Email"), required=False)

    def __init__(self, original_email=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_email = original_email

    def clean(self):
        super().clean()
        email = self.cleaned_data.get("email")
        confirm_email = self.cleaned_data.get("confirm_email")

        if email and email != self.original_email and email != confirm_email:
            raise forms.ValidationError({"confirm_email": _("Email addresses do not match.")})
