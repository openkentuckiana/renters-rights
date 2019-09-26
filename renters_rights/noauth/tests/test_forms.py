from django.test import TestCase
from hamcrest import assert_that, has_key

from noauth.forms import CodeForm, LoginForm


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
