import json

import boto3
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, View

from lib.mixins import AjaxableResponseMixin
from lib.views import ProtectedView
from units.forms import UnitForm
from units.models import Unit


class IndexView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return render(request, "index-logged-out.html")

        return render(request, "index.html")


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
    form_class = UnitForm
    success_url = "/units/"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


@login_required
def sign_files(request):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    )

    resp = {}
    for f in json.loads(request.body)["files"]:
        resp[f] = s3.generate_presigned_post(
            Bucket=settings.AWS_UPLOAD_BUCKET_NAME,
            Key=f"{request.user.username}/{f}",
            Fields={"acl": "private", "Content-Type": "image/png"},
            Conditions=[{"acl": "private"}, {"Content-Type": "image/png"}, ["content-length-range", 5000, 15000000]],
            ExpiresIn=3600,
        )
        # If we're running locally, make sure to return URLs that can be access from the front-end
        if settings.AWS_S3_ENDPOINT_URL and settings.AWS_S3_CUSTOM_DOMAIN:
            resp[f]["url"] = resp[f]["url"].replace("http://s3", "http://localhost")

    return JsonResponse(resp)
