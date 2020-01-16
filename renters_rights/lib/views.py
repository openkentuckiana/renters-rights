from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import View

from noauth.models import AuthCode


@method_decorator(login_required, name="dispatch")
class ProtectedView(View):
    pass


def get_next_page_from_request(request: HttpRequest, default_next: str):
    next_page = request.GET.get("next", None)
    if next_page == "gs":
        return reverse_lazy("get-started")

    return default_next
