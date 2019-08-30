import json
from concurrent.futures import FIRST_EXCEPTION, wait
from concurrent.futures.thread import ThreadPoolExecutor

import boto3
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, FormView, ListView, View

from lib.views import ProtectedView
from units.forms import UnitAddImageForm, UnitForm
from units.models import DOCUMENT, Unit, UnitImage


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
    success_url = reverse_lazy("unit-list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class UnitAddDocuments(FormView):
    """Handles the login form where users enter their email addresses to start the login process.
    After entering an email address, the user will be sent a log in link and code they can use to log in without a password.
    If a user doesn't exist, a user is created."""

    template_name = "units/unit_add_image.html"
    form_class = UnitAddImageForm

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        unit = Unit.objects.get_for_user(self.request.user, id=self.kwargs["unit_id"])
        form_kwargs["unit"] = unit
        form_kwargs["label"] = _("Documents")
        form_kwargs["max_images"] = settings.MAX_DOCUMENTS_PER_UNIT
        form_kwargs["current_image_count"] = UnitImage.objects.for_user(self.request.user, unit=unit).count()
        return form_kwargs

    def download_image(self, path, unit):
        if not path:
            return None

        # Make sure we only get images from the user's folder
        path = f"{unit.owner.username}/{path}"

        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        )
        s3_response_object = s3.get_object(Bucket=settings.AWS_UPLOAD_BUCKET_NAME, Key=path)
        file = s3_response_object["Body"].read()
        return InMemoryUploadedFile(ContentFile(file), None, path, "image/png", len(file), None)

    def create_image(self, img, image_type, unit, download=False):
        if not img:
            return
        if download:
            img = self.download_image(img, unit)
        UnitImage.objects.create(image=img, image_type=image_type, owner=unit.owner, unit=unit)

    def form_valid(self, form):
        # Multithreading image creation can really speed up this request, but uses o(n) memory, which can be
        # problematic on Heroku
        with ThreadPoolExecutor(max_workers=settings.MAX_THREAD_POOL_WORKERS) as executor:
            futures = []
            if form.files:
                for image in form.files.getlist("images"):
                    futures.append(executor.submit(self.create_image, image, DOCUMENT, form.unit))
            for path in form.data.get("s3_images", "").split(","):
                futures.append(executor.submit(self.create_image, path, DOCUMENT, form.unit, True))
            wait(futures, return_when=FIRST_EXCEPTION)
            for f in futures:
                if f.exception():
                    raise f.exception()
        return redirect(reverse_lazy("unit-list"))


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
