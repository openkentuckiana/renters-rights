from django.shortcuts import render
from django.views.generic import CreateView, View

from units.forms import UnitForm


class IndexView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return render(request, "index-logged-out.html")

        return render(request, "index.html")


class AnotherView(View):
    def get(self, request):
        return render(request, "another.html")


class UnitFormView(CreateView):
    template_name = "unit_form.html"
    form_class = UnitForm
    success_url = "/"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)
