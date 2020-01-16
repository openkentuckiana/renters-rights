import string
from secrets import choice

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.core.mail import EmailMultiAlternatives
from django.forms import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic.edit import FormView

from lib.views import ProtectedView

from .forms import CodeForm, ConfirmUsernameChangeForm, LoginForm, UserProfileForm
from .models import AuthCode, User


def normalize_email(email):
    return email.lower().strip() if email else None


class CodeView(View):
    """Handles the code form where the user enters their email address and code to authenticate.
    Accepts values either via querystring in a GET or in a form POST.
    """

    form_class = CodeForm
    template_name = "code.html"
    success_url = "/"

    def get(self, request, *args, **kwargs):
        email = normalize_email(self.request.GET.get("email"))
        code = self.request.GET.get("code")

        if email and code:
            form = self.form_class({"email": email, "code": code}, initial={"email": email, "code": code})
        else:
            form = self.form_class(initial={"email": email, "code": code})

        if email and code and form.is_valid():
            auth_code = self._validate_and_get_auth_code(email, code)
            if auth_code:
                login(request, auth_code.user)
                messages.add_message(request, messages.SUCCESS, _("You have been logged in."))
                return redirect(auth_code.next_page)
            form.add_error(None, ValidationError(_("Invalid e-mail address or code."), code="invalid_email_or_code"))

        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            email = normalize_email(form.cleaned_data["email"])
            code = form.cleaned_data["code"]
            auth_code = self._validate_and_get_auth_code(email, code)
            if auth_code:
                login(request, auth_code.user)
                messages.add_message(request, messages.SUCCESS, _("You have been logged in."))
                return redirect(self._get_next_page_from_auth_code(auth_code))

            form.add_error(None, ValidationError(_("Invalid e-mail address or code."), code="invalid_email_or_code"))

        return render(request, self.template_name, {"form": form})

    @classmethod
    def _validate_and_get_auth_code(cls, email, code):
        """Validates an code and returns a URI to redirect to, if the code is valid.

        Args:
          email: The email address associated with the auth code.
          code: The code associated with the auth code.

        Returns:
          A URI to redirect to if the code is valid, otherwise None.

        """
        auth_code = AuthCode.get_auth_code(email, code)
        if not auth_code:
            return None
        auth_code.delete()
        return auth_code

    @staticmethod
    def _get_next_page_from_auth_code(auth_code: AuthCode):
        """Gets the next page from an AuthCode object.
        If the next page is a page that has a next=gs query string parameter, we should redirect to the getting
        started page, rather than to the destination page. This happens when a user follows a link that requires
        authentication from the getting started page. It makes more sense for the user to go back to the getting started
        page, which will be populated with their data after logging in.

        Args:
          auth_code: the AuthCode object used to log a user in.

        Returns: the next page a user should be redirected to.
        """
        if "?next=gs" in auth_code.next_page:
            return reverse_lazy("get-started")

        return auth_code.next_page


class LogInView(FormView):
    """Handles the login form where users enter their email addresses to start the login process.
    After entering an email address, the user will be sent a log in link and code they can use to log in without a password.
    If a user doesn't exist, a user is created.
    """

    template_name = "log-in.html"
    form_class = LoginForm
    success_url = reverse_lazy("noauth:code")

    def form_valid(self, form):
        email = normalize_email(form.cleaned_data["email"])
        user = self.get_user(email)
        if not user:
            user = self.create_user(email)

        if AuthCode.send_auth_code(user, self.request.build_absolute_uri(reverse("noauth:code")), self.request.GET.get("next")):
            self.success_url += f"?email={user.username}"
            return super().form_valid(form)
        else:
            form.add_error(None, _("Please check your inbox and spam folder for a previously-sent code."))
            return super().form_invalid(form)

    def create_user(self, email):
        # password should never be used by a user to log in. Just make it long and random.
        password = "".join(choice(string.ascii_letters + string.digits) for i in range(50))
        return User.objects.create_user(email, email, password)

    def get_user(self, email):
        try:
            return User.objects.get(username=email)
        except User.DoesNotExist:
            return None


class LogOutView(View):
    template_name = "log-out.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        messages.add_message(request, messages.SUCCESS, _("You have been logged out."))
        logout(request)
        return HttpResponseRedirect(reverse("homepage"))


class UserProfileView(FormView, ProtectedView):
    template_name = "account-details.html"
    form_class = UserProfileForm
    success_url = reverse_lazy("noauth:account-details")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["original_username"] = self.request.user.username
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial["first_name"] = self.request.user.first_name
        initial["last_name"] = self.request.user.last_name
        initial["email"] = self.request.user.username
        return initial

    def form_valid(self, form):
        user = self.request.user
        new_username = form.cleaned_data.get("email")
        current_username = user.username

        if new_username and new_username != current_username:
            code = AuthCode.generate_code()

            User.objects.filter(id=user.id).update(
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                pending_new_email=new_username,
                pending_code=code,
                pending_code_timestamp=timezone.now(),
            )

            email_context = {
                "confirmation_uri": self.request.build_absolute_uri(reverse("noauth:confirm-username-change")),
                "code": code,
                "old_username": current_username,
                "new_username": new_username,
                "site_name": settings.SITE_NAME,
            }

            template = "username-pending-change-email.txt"
            html_template = "username-pending-change-email.html"

            subject, to = (_(f"Your requested {settings.SITE_NAME} email change"), current_username)
            msg = EmailMultiAlternatives(subject, render_to_string(template, email_context), None, [to])
            msg.attach_alternative(render_to_string(html_template, email_context), "text/html")
            msg.send()

            messages.add_message(
                self.request, messages.SUCCESS, _("Your changes were saved. Check your email to complete username change.")
            )
            self.success_url = reverse_lazy("noauth:confirm-username-change")
        else:
            User.objects.filter(id=user.id).update(
                first_name=form.cleaned_data["first_name"], last_name=form.cleaned_data["last_name"]
            )
            messages.add_message(self.request, messages.SUCCESS, _("Your changes were saved."))
        return super().form_valid(form)


class ConfirmUsernameChangeView(FormView, ProtectedView):
    template_name = "username-pending-change.html"
    form_class = ConfirmUsernameChangeForm
    success_url = reverse_lazy("noauth:account-details")

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pending_new_email"] = self.request.user.pending_new_email
        context["current_username"] = self.request.user.username
        return context

    def get_initial(self):
        initial = super().get_initial()
        initial["code"] = self.request.GET.get("code")
        return initial

    def form_valid(self, form):
        user = self.request.user

        current_username = user.username
        new_username = user.pending_new_email

        email_context = {"new_username": new_username, "site_name": settings.SITE_NAME}

        template = "username-changed-email.txt"
        html_template = "username-changed-email.html"

        subject, to = (_(f"Your {settings.SITE_NAME} email has changed"), current_username)
        msg = EmailMultiAlternatives(subject, render_to_string(template, email_context), None, [to])
        msg.attach_alternative(render_to_string(html_template, email_context), "text/html")
        msg.send()

        previous_emails = user.previous_emails
        previous_emails.append(current_username)

        User.objects.filter(id=user.id).update(
            username=new_username,
            email=new_username,
            previous_emails=previous_emails,
            pending_new_email=None,
            pending_code=None,
            pending_code_timestamp=None,
        )

        messages.add_message(self.request, messages.SUCCESS, _("Your username was changed."))

        return super().form_valid(form)
