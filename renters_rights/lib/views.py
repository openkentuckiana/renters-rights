from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import View


@method_decorator(login_required, name="dispatch")
class ProtectedView(View):
    pass


def get_next(request, default_next):
    next_page = request.GET.get("next", None)
    if next_page == "gs":
        return reverse_lazy("get-started")

    return default_next
