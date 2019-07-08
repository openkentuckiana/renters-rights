from django.shortcuts import render
from django.views.generic import CreateView, DetailView, ListView, View

from units.forms import UnitForm
from units.models import Unit


class IndexView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return render(request, "index-logged-out.html")

        return render(request, "index.html")


class AnotherView(View):
    def get(self, request):
        return render(request, "another.html")


class UnitListView(ListView):
    model = Unit
    context_object_name = "unit_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model"] = self.model
        return context


class UnitDetailView(DetailView):
    model = Unit


class UnitCreateFormView(CreateView):
    template_name = "units/unit_form.html"
    form_class = UnitForm
    success_url = "/"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)
