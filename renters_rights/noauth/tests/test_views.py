import datetime
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext as _
from freezegun import freeze_time
from hamcrest import assert_that, contains, equal_to, has_key, none

# from districts.models import District
from noauth.forms import CodeForm
from noauth.models import AuthCode, User
from noauth.tests import UnitBaseTestCase
from noauth.views import CodeView


class CodeViewTests(UnitBaseTestCase):
    view_url = reverse("noauth:code")

    def test_get_with_code_and_no_email_returns_blank_form(self):
        response = self.client.get(f"{self.view_url}?code=1")
        form = response.context["form"]
        assert_that(form.initial, has_key("email"))
        assert_that(form.initial["email"], none())
        self.assertTrue(isinstance(form, CodeForm))

    def test_get_with_email_and_no_code_returns_form_with_email(self):
        response = self.client.get(f"{self.view_url}?email=a")
        form = response.context["form"]
        assert_that(form.initial, has_key("email"))
        assert_that(form.initial["email"], equal_to("a"))
        self.assertTrue(isinstance(form, CodeForm))

    @patch("noauth.views.CodeView._validate_and_get_auth_code")
    def test_get_with_code_and_email_calls_validate_method(self, m_validate_and_get_auth_code):
        m_validate_and_get_auth_code.return_value = None

        self.client.get(f"{self.view_url}?email=a@example.com&code=1")

        m_validate_and_get_auth_code.assert_called_once_with("a@example.com", "1")

    @patch("noauth.views.CodeView._validate_and_get_auth_code")
    def test_post_with_code_and_email_calls_validate_method(self, m_validate_and_get_auth_code):
        m_validate_and_get_auth_code.return_value = None

        self.client.post(self.view_url, {"email": "a@example.com", "code": 1})

        m_validate_and_get_auth_code.assert_called_once_with("a@example.com", "1")

    @patch("noauth.views.CodeView._validate_and_get_auth_code")
    def test_get_with_invalid_data_returns_error(self, m_validate_and_get_auth_code):
        m_validate_and_get_auth_code.return_value = None
        response = self.client.get(f"{self.view_url}?email=a@example.com&code=1")
        self.assertFormError(response, "form", None, _("Invalid e-mail address or code."))

    @patch("noauth.views.CodeView._validate_and_get_auth_code")
    def test_post_with_invalid_data_returns_error(self, m_validate_and_get_auth_code):
        m_validate_and_get_auth_code.return_value = None
        response = self.client.post(self.view_url, {"email": "a@example.com", "code": "1"})
        self.assertFormError(response, "form", None, _("Invalid e-mail address or code."))

    @override_settings(NOAUTH_CODE_TTL_MINUTES=5)
    def test_validate_and_get_redirect_uri_returns_default_path_with_get(self):
        code = 1234

        with freeze_time("09-17-2018 6:30PM") as frozen_datetime:
            AuthCode.objects.create(user=CodeViewTests.u, code=code)

            frozen_datetime.tick(delta=datetime.timedelta(minutes=4))

            response = self.client.get(f"{self.view_url}?code={code}&email={CodeViewTests.u.username}")
            self.assertRedirects(response, reverse("homepage"))

    @override_settings(NOAUTH_CODE_TTL_MINUTES=5)
    def test_validate_and_get_redirect_uri_returns_default_path_with_post(self):
        code = 1234

        with freeze_time("09-17-2018 6:30PM") as frozen_datetime:
            AuthCode.objects.create(user=CodeViewTests.u, code=code)

            frozen_datetime.tick(delta=datetime.timedelta(minutes=4))

            response = self.client.post(self.view_url, {"code": code, "email": CodeViewTests.u.username})
            self.assertRedirects(response, reverse("homepage"))

    @override_settings(NOAUTH_CODE_TTL_MINUTES=5)
    def test_validate_and_get_redirect_uri_returns_next_page_from_auth_code_with_get(self):
        code = 1234
        next_page = f"{reverse('homepage')}?and=something"

        with freeze_time("09-17-2018 6:30PM") as frozen_datetime:
            AuthCode.objects.create(user=CodeViewTests.u, code=code, next_page=next_page)

            frozen_datetime.tick(delta=datetime.timedelta(minutes=4))

            response = self.client.get(f"{self.view_url}?code={code}&email={CodeViewTests.u.username}")
            self.assertRedirects(response, next_page)

    @override_settings(NOAUTH_CODE_TTL_MINUTES=5)
    def test_validate_and_get_redirect_uri_returns_next_page_from_auth_code_with_post(self):
        code = 1234
        next_page = f"{reverse('homepage')}?and=something"

        with freeze_time("09-17-2018 6:30PM") as frozen_datetime:
            AuthCode.objects.create(user=CodeViewTests.u, code=code, next_page=next_page)

            frozen_datetime.tick(delta=datetime.timedelta(minutes=4))

            response = self.client.post(self.view_url, {"code": code, "email": CodeViewTests.u.username})
            self.assertRedirects(response, next_page)

    @override_settings(NOAUTH_CODE_TTL_MINUTES=5)
    def test_validate_and_get_redirect_uri_does_not_find_auth_code_if_ttl_past(self):
        code = 1234

        with freeze_time("09-17-2018 6:30PM") as frozen_datetime:
            AuthCode.objects.create(user=CodeViewTests.u, code=code)

            frozen_datetime.tick(delta=datetime.timedelta(minutes=6))

            redirect_url = CodeView._validate_and_get_auth_code(CodeViewTests.u.email, code)
            assert_that(redirect_url, none())


class LoginViewTests(UnitBaseTestCase):
    view_url = reverse("noauth:log-in")

    @patch("noauth.models.AuthCode.send_auth_code")
    def test_posting_a_user_that_does_not_exist_creates_user(self, m_send_auth_code):
        m_send_auth_code.return_value = True
        email = f"jason.mendoza@goodplace.com"
        assert_that(User.objects.filter(email=email).exists(), equal_to(False))
        self.client.post(self.view_url, {"email": email})
        assert_that(User.objects.filter(email=email).exists(), equal_to(True))

    @patch("noauth.models.AuthCode.send_auth_code")
    def test_posting_a_user_who_has_not_received_an_auth_code_sends_auth_code_and_redirects_to_code_page(
        self, m_send_auth_code
    ):
        m_send_auth_code.return_value = True
        response = self.client.post(self.view_url, {"email": LoginViewTests.u.username})
        m_send_auth_code.assert_called_once_with(LoginViewTests.u, f"http://testserver{reverse('noauth:code')}")
        self.assertRedirects(response, reverse("noauth:code") + f"?email={LoginViewTests.u.username}")

    @patch("noauth.models.AuthCode.send_auth_code")
    def test_posting_a_user_who_has_received_an_auth_code_returns_error(self, m_send_auth_code):
        m_send_auth_code.return_value = False
        response = self.client.post(self.view_url, {"email": LoginViewTests.u.username})
        m_send_auth_code.assert_called_once_with(LoginViewTests.u, f"http://testserver{reverse('noauth:code')}")
        assert_that(response.context["form"].errors, has_key("__all__"))
        assert_that(
            response.context["form"].errors["__all__"],
            contains(_("Please check your inbox and spam folder for a previously-sent code.")),
        )
