from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import View


@method_decorator(login_required, name="dispatch")
class ProtectedView(View):
    pass
