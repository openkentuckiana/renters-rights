from django.shortcuts import render
from django.views.generic import (CreateView, DetailView, ListView, UpdateView,
                                  View)

from lib.views import ProtectedView
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

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Unit.objects.for_user(self.request.user)
        else:
            return Unit.objects.none()


class UnitDetailView(DetailView, ProtectedView):
    model = Unit

    def get_queryset(self):
        return Unit.objects.for_user(self.request.user)


class UnitCreate(CreateView, ProtectedView):
    template_name = "units/unit_form.html"
    model = Unit
    fields = [
        "unit_address_1",
        "unit_address_2",
        "unit_city",
        "unit_state",
        "unit_zip_code",
        "landlord_address_1",
        "landlord_address_2",
        "landlord_city",
        "landlord_state",
        "landlord_zip_code",
        "landlord_phone_number",
        "lease_start_date",
        "lease_end_date",
        "rent_due_date",
    ]
    success_url = "/"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


# class UnitCreate(CreateView, ProtectedView):
#     template_name = "units/unit_form.html"
#     form_class = UnitForm
#     success_url = "/"
#
#     def form_valid(self, form):
#         form.instance.owner = self.request.user
#         return super().form_valid(form)

# class UnitUpdate(UpdateView, ProtectedView):
#     template_name = "units/unit_form.html"
#     form_class = UnitForm
#     success_url = "/"
#
#     def form_valid(self, form):
#         form.instance.owner = self.request.user
#         return super().form_valid(form)
