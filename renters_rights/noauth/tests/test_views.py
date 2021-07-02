import datetime
from unittest.mock import patch

from django.conf import settings
from django.core import mail
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from freezegun import freeze_time
from hamcrest import assert_that, contains, contains_string, equal_to, has_key, is_not, none

from noauth.forms import CodeForm, ConfirmUsernameChangeForm, UserProfileForm
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
        m_send_auth_code.assert_called_once_with(LoginViewTests.u, f"http://testserver{reverse('noauth:code')}", None)
        self.assertRedirects(response, reverse("noauth:code") + f"?email={LoginViewTests.u.username}")

    @patch("noauth.models.AuthCode.send_auth_code")
    def test_posting_a_user_who_has_received_an_auth_code_adds_message_and_redirects(self, m_send_auth_code):
        m_send_auth_code.return_value = False
        response = self.client.post(self.view_url, {"email": LoginViewTests.u.username})
        m_send_auth_code.assert_called_once_with(LoginViewTests.u, f"http://testserver{reverse('noauth:code')}", None)
        self.assertRedirects(response, reverse("noauth:code") + f"?email={LoginViewTests.u.username}")
        # breakpoint()
        # assert_that(
        #     response.context["messages"], contains(_("Please check your inbox and spam folder for a previously-sent code."))
        # )


class LogOutViewTests(UnitBaseTestCase):
    view_url = reverse("noauth:log-out")

    def test_get_returns_log_out_page(self):
        response = self.client.get(self.view_url)
        self.assertContains(response, _("Cancel"))
        self.assertContains(response, _("Log Out"))

    def test_posting_a_user_that_does_not_exist_creates_user(self):
        c = Client()
        c.force_login(LogOutViewTests.u)
        response = c.post(self.view_url)
        self.assertRedirects(response, reverse("homepage"))


class UserProfileViewTests(UnitBaseTestCase):
    view_url = reverse("noauth:account-details")

    def test_user_profile_view_requires_login(self):
        response = self.client.get(self.view_url)
        self.assertRedirects(response, f"{reverse('noauth:log-in')}?next={self.view_url}")

    def test_get_returns_form_with_user_info_as_initial_values(self):
        c = Client()
        c.force_login(UserProfileViewTests.u)
        response = c.get(self.view_url)
        form = response.context["form"]
        assert_that(form.initial, has_key("email"))
        assert_that(form.initial["email"], equal_to(UserProfileViewTests.u.username))
        assert_that(form.initial, has_key("first_name"))
        assert_that(form.initial["first_name"], equal_to(UserProfileViewTests.u.first_name))
        assert_that(form.initial, has_key("last_name"))
        assert_that(form.initial["last_name"], equal_to(UserProfileViewTests.u.last_name))
        self.assertTrue(isinstance(form, UserProfileForm))

    def test_username_change(self):
        """When a user submits a new username, the app should set the pending fields and send an email."""
        user = UserProfileViewTests.u
        original_username = user.username

        c = Client()
        c.force_login(user)
        response = c.post(
            self.view_url,
            {
                "first_name": "Tahani",
                "last_name": "Al-Jamil",
                "email": "tahani@goodplace.net",
                "confirm_email": "tahani@goodplace.net",
            },
        )

        user.refresh_from_db()

        # Should be changed
        assert_that(user.first_name, equal_to("Tahani"))
        assert_that(user.last_name, equal_to("Al-Jamil"))

        # Should not be changed yet
        assert_that(user.username, equal_to(original_username))
        assert_that(user.email, equal_to(original_username))

        # Should be set to allow confirmation of username change
        assert_that(user.pending_new_email, equal_to("tahani@goodplace.net"))
        assert_that(user.pending_code, is_not(none()))
        assert_that(user.pending_code_timestamp, is_not(none()))

        assert_that(len(mail.outbox), equal_to(1))
        assert_that(mail.outbox[0].subject, equal_to(_(f"Your requested {settings.SITE_NAME} email change")))
        assert_that(mail.outbox[0].body, contains_string(user.pending_code))

        self.assertRedirects(response, reverse("noauth:confirm-username-change"))

    def test_non_username_change(self):
        user = UserProfileViewTests.u
        original_username = user.username

        c = Client()
        c.force_login(user)
        response = c.post(self.view_url, {"first_name": "Tahani", "last_name": "Al-Jamil", "email": original_username})

        user.refresh_from_db()

        # Should be changed
        assert_that(user.first_name, equal_to("Tahani"))
        assert_that(user.last_name, equal_to("Al-Jamil"))

        # Should not be changed
        assert_that(user.username, equal_to(original_username))
        assert_that(user.email, equal_to(original_username))

        # Should not be set
        assert_that(user.pending_new_email, none())
        assert_that(user.pending_code, none())
        assert_that(user.pending_code_timestamp, none())

        assert_that(len(mail.outbox), equal_to(0))

        self.assertRedirects(response, self.view_url)


class ConfirmUsernameChangeViewTests(UnitBaseTestCase):
    view_url = reverse("noauth:confirm-username-change")

    def test_confirm_username_change_view_requires_login(self):
        response = self.client.get(self.view_url)
        self.assertRedirects(response, f"{reverse('noauth:log-in')}?next={self.view_url}")

    def test_get_returns_blank_form(self):
        c = Client()
        c.force_login(ConfirmUsernameChangeViewTests.u)
        response = c.get(self.view_url)
        form = response.context["form"]
        assert_that(form.initial, has_key("code"))
        assert_that(form.initial["code"], none())
        self.assertTrue(isinstance(form, ConfirmUsernameChangeForm))

    def test_get_with_code_param_returns_populated_form(self):
        c = Client()
        c.force_login(ConfirmUsernameChangeViewTests.u)
        response = c.get(f"{self.view_url}?code=1234")
        form = response.context["form"]
        assert_that(form.initial, has_key("code"))
        assert_that(form.initial["code"], equal_to("1234"))
        self.assertTrue(isinstance(form, ConfirmUsernameChangeForm))

    def test_username_changed_with_valid_code(self):
        user = ConfirmUsernameChangeViewTests.u

        new_username = "tahani@goodplace.net"

        User.objects.filter(id=user.id).update(
            **{
                "pending_new_email": new_username,
                "pending_code": "1234",
                "pending_code_timestamp": timezone.now() + datetime.timedelta(hours=1),
            }
        )

        c = Client()
        c.force_login(user)

        response = c.post(self.view_url, {"code": "1234"})

        user.refresh_from_db()

        assert_that(user.username, equal_to(new_username))
        assert_that(user.email, equal_to(new_username))
        assert_that(user.pending_new_email, none())
        assert_that(user.pending_code, none())
        assert_that(user.pending_code_timestamp, none())

        self.assertRedirects(response, reverse("noauth:account-details"))
