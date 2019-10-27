import datetime

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from hamcrest import assert_that, contains_string, equal_to, has_key

from noauth.forms import CodeForm, ConfirmUsernameChangeForm, LoginForm, UserProfileForm
from noauth.models import User


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


class UserProfileFormTests(TestCase):
    def test_verify_first_name_last_name_and_same_email_are_valid(self):
        original_username = "jane@domain.com"
        data = {"first_name": "Jane", "last_name": "Goodall", "email": original_username}
        form = UserProfileForm(original_username=original_username, data=data)
        self.assertTrue(form.is_valid())

    def test_verify_first_name_last_name_and_differing_new_emails_is_invalid(self):
        original_username = "jane@domain.com"
        data = {"first_name": "Jane", "last_name": "Goodall", "email": "jane2@domain.com", "confirm_email": "jane3@domain.com"}
        form = UserProfileForm(original_username=original_username, data=data)
        self.assertFalse(form.is_valid())
        assert_that(form.errors, has_key("confirm_email"))
        assert_that(form.errors["confirm_email"][0], contains_string("Email addresses do not match."))

    def test_verify_first_name_last_name_and_in_user_new_email_is_invalid(self):
        User.objects.create(username="jane2@domain.com")

        original_username = "jane@domain.com"
        data = {"first_name": "Jane", "last_name": "Goodall", "email": "jane2@domain.com", "confirm_email": "jane2@domain.com"}
        form = UserProfileForm(original_username=original_username, data=data)
        self.assertFalse(form.is_valid())
        assert_that(form.errors, has_key("email"))
        assert_that(form.errors["email"][0], contains_string("Email addresses already in use."))


class ConfirmUsernameChangeFormTests(TestCase):
    def setUp(self):
        self.u = User(
            pending_new_email="new@example.com",
            pending_code="1234",
            pending_code_timestamp=timezone.now() + datetime.timedelta(hours=1),
        )

    def test_verify_valid_code_is_valid(self):
        data = {"code": "1234"}
        form = ConfirmUsernameChangeForm(user=self.u, data=data)
        self.assertTrue(form.is_valid())

    def test_verify_invalid_code_is_invalid(self):
        data = {"code": "0987"}
        form = ConfirmUsernameChangeForm(user=self.u, data=data)
        self.assertFalse(form.is_valid())
        assert_that(form.errors, has_key("code"))
        assert_that(form.errors["code"][0], contains_string("The code you entered is invalid."))

    def test_verify_expired_code_is_invalid(self):
        data = {"code": "1234"}
        self.u.pending_code_timestamp = timezone.now() - datetime.timedelta(hours=9999)
        form = ConfirmUsernameChangeForm(user=self.u, data=data)
        self.assertFalse(form.is_valid())
        assert_that(form.errors, has_key("code"))
        assert_that(
            form.errors["code"][0],
            contains_string(f"Code is expired. Please confirm change within {settings.NOAUTH_CODE_TTL_MINUTES} minutes."),
        )
