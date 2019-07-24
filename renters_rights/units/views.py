import json

import boto3
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from lib.mixins import AjaxableResponseMixin
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


class UnitCreate(AjaxableResponseMixin, CreateView, ProtectedView):
    template_name = "units/unit_form.html"
    form_class = UnitForm
    success_url = "/units/"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


def sign_files(request):
    s3 = boto3.client("s3", aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    resp = {}
    for f in json.loads(request.body)["files"]:
        resp[f] = s3.generate_presigned_post(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=f,
            Fields={
                "acl": "private",
                "Content-Type": "image/png",
                # "content_length_range": (5000, 5000000),
            },
            Conditions=[
                {"acl": "private"},
                {"Content-Type": "image/png"},
                # {"content_length_range": (5000, 5000000)}
            ],
            ExpiresIn=3600,
        )

    return JsonResponse(resp)


#
# class UnitUpdate(UpdateView, ProtectedView):
#     template_name = "units/unit_form.html"
#     form_class = UnitForm
#     success_url = "/units/"
#
#     def form_valid(self, form):
#         form.instance.owner = self.request.user
#         return super().form_valid(form)
