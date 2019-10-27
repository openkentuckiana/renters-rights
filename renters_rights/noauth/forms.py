import datetime

from django import forms
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from noauth.models import User


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

    def __init__(self, original_username=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def clean(self):
        super().clean()
        email = self.cleaned_data.get("email")
        confirm_email = self.cleaned_data.get("confirm_email")

        if email and email != self.original_username and email != confirm_email:
            raise forms.ValidationError({"confirm_email": _("Email addresses do not match.")})

        if (
            email
            and email != self.original_username
            and email == confirm_email
            and User.objects.filter(username=email).count() > 0
        ):
            raise forms.ValidationError({"email": _("Email addresses already in use.")})


class ConfirmUsernameChangeForm(forms.Form):
    code = forms.CharField(label="Code", max_length=20, required=True)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_code(self):
        code = self.cleaned_data.get("code")

        if not self.user.pending_code:
            raise forms.ValidationError(_("You do not have a pending username change."))

        if not self.user.pending_code == code.strip():
            raise forms.ValidationError(_("The code you entered is invalid."))

        if self.user.pending_code_timestamp and timezone.now() - self.user.pending_code_timestamp > datetime.timedelta(
            minutes=settings.NOAUTH_CODE_TTL_MINUTES
        ):
            raise forms.ValidationError(
                _("Code is expired. Please confirm change within %(minutes)s minutes.")
                % {"minutes": settings.NOAUTH_CODE_TTL_MINUTES}
            )
