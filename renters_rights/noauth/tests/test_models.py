import mock
from django.conf import settings
from django.core import mail
from django.template.loader import render_to_string
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _
from hamcrest import assert_that, equal_to, none

from noauth.models import DEFAULT_CODE_LENGTH, AuthCode, User


class AuthCodeModelTests(TestCase):
    def setUp(self):
        self.u = User.objects.create(is_active=True, email="eleanor@shellstrop.com")

    def test_create_code_for_user_returns_none_for_inactive_user(self):
        self.u.is_active = False
        self.u.save()
        assert_that(AuthCode._create_code_for_user(self.u), none())

    def test_create_code_for_user_creates_new_code(self):
        expected_auth_code = AuthCode._create_code_for_user(self.u)
        actual_auth_code = AuthCode.objects.get(user=self.u, code=expected_auth_code.code)
        assert_that(expected_auth_code.code, equal_to(actual_auth_code.code))

    def test_generate_code_creates_code_of_default_length(self):
        code = AuthCode._create_code_for_user(self.u).code
        assert_that(len(code), equal_to(DEFAULT_CODE_LENGTH))

    @override_settings(NOAUTH_CODE_LENGTH=19)
    def test_generate_code_creates_code_of_length_defined_in_settings(self):
        code = AuthCode._create_code_for_user(self.u).code
        assert_that(len(code), equal_to(19))

    @mock.patch("noauth.models.AuthCode._create_code_for_user")
    def test_send_auth_code_returns_false_when_auth_code_not_created(self, m_create_code_for_user):
        m_create_code_for_user.return_value = False
        self.assertFalse(AuthCode.send_auth_code(self.u, ""))

    @mock.patch("noauth.models.AuthCode._create_code_for_user")
    def test_send_auth_code_returns_false_when_auth_code_not_created(self, m_create_code_for_user):
        auth_code = AuthCode(code="123", user=self.u)
        m_create_code_for_user.return_value = auth_code
        self.assertTrue(AuthCode.send_auth_code(self.u, "http://site/code?code=123"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, _(f"Your {settings.SITE_NAME} log in code"))

        context = {
            "code": auth_code.code,
            "code_uri": "http://site/code?code=123",
            "email": auth_code.user.email,
            "site_name": settings.SITE_NAME,
        }
        assert_that(mail.outbox[0].body, equal_to(render_to_string("log-in-email.txt", context)))
        assert_that(mail.outbox[0].alternatives[0][0], equal_to(render_to_string("log-in-email.html", context)))
