import string
from secrets import choice

from django.contrib.auth import login
from django.forms import ValidationError
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic.edit import FormView

from .forms import CodeForm, LoginForm
from .models import AuthCode, User


class CodeView(View):
    """
    Handles the code form where the user enters their email address and code to authenticate.
    Accepts values either via querystring in a GET or in a form POST.
    """

    form_class = CodeForm
    template_name = "code.html"
    success_url = "/"

    def get(self, request, *args, **kwargs):
        email = self.request.GET.get("email")
        code = self.request.GET.get("code")

        if email and code:
            next_page = self._validate_and_get_auth_code(email, code)
            if next_page:
                return redirect(next_page)

        form = self.form_class(initial={"email": email})
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            code = form.cleaned_data["code"]
            auth_code = self._validate_and_get_auth_code(email, code)
            if auth_code:
                import pdb; pdb.set_trace()
                login(request, auth_code.user)
                return redirect(auth_code.next_page)

            form.add_error(
                None,
                ValidationError(
                    _("Invalid e-mail address or code."), code="invalid_email_or_code"
                ),
            )

        return render(request, self.template_name, {"form": form})

    @classmethod
    def _validate_and_get_auth_code(cls, email, code):
        """
        Validates an code and returns a URI to redirect to, if the code is valid.
        :param email: The email address associated with the auth code.
        :param code: The code associated with the auth code.
        :return: A URI to redirect to if the code is valid, otherwise None.
        """
        auth_code = AuthCode.get_auth_code(email, code)
        if not auth_code:
            return None
        auth_code.delete()
        return auth_code


class LoginView(FormView):
    """Handles the login form where users enter their email addresses to start the login process.
    After entering an email address, the user will be sent a log in link and code they can use to log in without a password.
    If a user doesn't exist, a user is created."""

    template_name = "login.html"
    form_class = LoginForm
    success_url = reverse_lazy("noauth:code")

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        user = self.get_user(email)
        if not user:
            user = self.create_user(email)

        if AuthCode.send_auth_code(user):
            self.success_url += f"?email={user.username}"
            return super().form_valid(form)
        else:
            form.add_error(
                None,
                _(
                    "Please check your inbox and spam folder for a previously-sent code."
                ),
            )
            return super().form_invalid(form)

    def create_user(self, email):
        # password should never be used by a user to log in. Just make it long and random.
        password = "".join(
            choice(string.ascii_letters + string.digits) for i in range(50)
        )
        return User.objects.create_user(email, email, password)

    def get_user(self, email):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
