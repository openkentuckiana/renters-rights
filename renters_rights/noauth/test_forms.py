import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from hamcrest import assert_that, has_key

from .forms import CodeForm, LoginForm


class LoginFormTests(TestCase):
    def test_verify_email_required(self):
        form = CodeForm(data={})
        self.assertFalse(form.is_valid())
        assert_that(form.errors, has_key("email"))

    def test_district1_email_accepted_as_valid(self):
        data = {"email": "jane@example1.com"}
        form = LoginForm(data)
        self.assertTrue(form.is_valid())

    def test_district2_email_accepted_as_valid(self):
        data = {"email": "jane@example2.com"}
        form = LoginForm(data)
        self.assertTrue(form.is_valid())

    def test_unknown_email_domain_rejected_as_invalid(self):
        data = {"email": "jane@unknown.com"}
        form = LoginForm(data)
        self.assertFalse(form.is_valid())

    def test_unknown_email_domain_error_message(self):
        data = {"email": "jane@unknown.com"}
        form = LoginForm(data)
        response = self.client.post(reverse("noauth:login"), data)
        self.assertFormError(
            response,
            "form",
            "email",
            _("Your email domain is not authorized to sign into this site."),
        )


class CodeFormTests(TestCase):
    def test_verify_email_and_code_are_accepted(self):
        data = {"email": "joe@domain.com", "code": 123}
        form = CodeForm(data)
        self.assertTrue(form.is_valid())

    def test_verify_email_required(self):
        data = {"code": 123}
        form = CodeForm(data)
        self.assertFalse(form.is_valid())
        assert_that(form.errors, has_key("email"))

    def test_verify_code_required(self):
        data = {"email": "joe@domain.com"}
        form = CodeForm(data)
        self.assertFalse(form.is_valid())
        assert_that(form.errors, has_key("code"))
