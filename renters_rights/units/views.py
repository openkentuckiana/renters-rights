import json
from concurrent.futures import FIRST_EXCEPTION, wait
from concurrent.futures.thread import ThreadPoolExecutor

import boto3
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, FormView, ListView, UpdateView, View

from documents.models import DocumentTemplate
from lib.views import ProtectedView, get_next_page_from_request
from units.forms import UnitAddImageForm, UnitForm
from units.models import DOCUMENT, MOVE_IN_PICTURE, MOVE_OUT_PICTURE, Unit, UnitImage


class IndexView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return render(request, "index-logged-out.html")

        units = Unit.objects.for_user(self.request.user)
        context = {
            "units": units,
            "num_units": len(units),
            "allow_new_unit_creation": len(units) < settings.MAX_UNITS,
            "picture_count": sum([u.unitimage_set.count() for u in units]),
            "document_list": DocumentTemplate.objects.filter(include_on_get_started=True),
        }

        return render(request, "index.html", context=context)


class GetStartedView(View):
    def get(self, request):
        context = {}
        if self.request.user.is_authenticated:
            units = Unit.objects.for_user(self.request.user)
            context = {
                "units": units,
                "num_units": len(units),
                "allow_new_unit_creation": len(units) < settings.MAX_UNITS,
                "picture_count": sum([u.unitimage_set.count() for u in units]),
                "document_list": DocumentTemplate.objects.all(),  # .filter(include_on_get_started=True),
            }

        return render(request, "get-started.html", context=context)


class UnitListView(ListView):
    model = Unit
    context_object_name = "unit_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model"] = self.model
        num_units = self.get_queryset().count()
        context["num_units"] = num_units
        context["allow_new_unit_creation"] = num_units < settings.MAX_UNITS
        context["CACHE_TIMEOUT"] = settings.CACHE_TIMEOUT
        return context

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Unit.objects.for_user(self.request.user)
        else:
            return Unit.objects.none()


class UnitDetailView(DetailView, ProtectedView):
    model = Unit

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["CACHE_TIMEOUT"] = settings.CACHE_TIMEOUT
        return context

    def get_queryset(self):
        return Unit.objects.for_user(self.request.user)


class UnitCreate(CreateView, ProtectedView):
    template_name = "units/unit_form.html"
    form_class = UnitForm
    # This can go away once we support multiple states. At that time, we should probably limit the list to states we support
    initial = {"unit_state": "KY"}

    def check_unit_limit(self):
        if self.request.user.is_authenticated and Unit.objects.for_user(self.request.user).count() >= settings.MAX_UNITS:
            messages.add_message(
                self.request, messages.ERROR, _("You have added the maximum number of units. Please delete a unit to continue.")
            )
            return HttpResponseRedirect(reverse("unit-list"))

    def get(self, request):
        return self.check_unit_limit() or super().get(request)

    def post(self, request):
        return self.check_unit_limit() or super().post(request)

    def form_valid(self, form):
        self.success_url = get_next_page_from_request(self.request, reverse_lazy("unit-list"))
        form.instance.owner = self.request.user
        return super().form_valid(form)


class UnitUpdate(UpdateView, ProtectedView):
    model = Unit
    template_name = "units/unit_form.html"
    form_class = UnitForm

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class UnitDeleteView(ProtectedView):
    def get(self, request, *args, **kwargs):
        unit = Unit.objects.get_for_user(self.request.user, slug=self.kwargs["slug"])
        return render(request, "units/unit_delete.html", {"unit": unit})

    def post(self, request, *args, **kwargs):
        unit = Unit.objects.get_for_user(self.request.user, slug=self.kwargs["slug"])
        unit.delete()
        messages.add_message(request, messages.SUCCESS, _("Unit successfully deleted."))
        return HttpResponseRedirect(reverse("unit-list"))


class UnitAddImagesFormViewBase(FormView, ProtectedView):
    template_name = "units/unit_add_image.html"
    form_class = UnitAddImageForm
    image_type = None

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        unit = Unit.objects.get_for_user(self.request.user, slug=self.kwargs["slug"])
        form_kwargs["unit"] = unit
        return form_kwargs

    def download_image(self, path, unit):
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
        # problematic on Heroku)
        with ThreadPoolExecutor(max_workers=settings.MAX_THREAD_POOL_WORKERS) as executor:
            futures = []
            if form.files:
                for image in form.files.getlist("images"):
                    futures.append(executor.submit(self.create_image, image, self.image_type, form.unit))
            for path in form.data.get("s3_images", "").split(","):
                futures.append(executor.submit(self.create_image, path, self.image_type, form.unit, True))
            wait(futures, return_when=FIRST_EXCEPTION)
            for f in futures:
                if f.exception():
                    raise f.exception()
        return redirect(get_next_page_from_request(self.request, reverse_lazy("unit-list")))


class UnitAddDocumentsFormView(UnitAddImagesFormViewBase):
    image_type = DOCUMENT

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["label"] = _("Documents")
        form_kwargs["upload_instructions"] = _("Take pictures of important documents to save for later. For example:")
        form_kwargs["upload_ideas"] = [_("Your lease"), _("An important letter from your landlord")]
        form_kwargs["max_images"] = settings.MAX_DOCUMENTS_PER_UNIT
        form_kwargs["current_image_count"] = UnitImage.objects.for_user(
            self.request.user, unit=form_kwargs["unit"], image_type=DOCUMENT
        ).count()
        return form_kwargs


class UnitAddMoveInPicturesFormView(UnitAddImagesFormViewBase):
    image_type = MOVE_IN_PICTURE

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["label"] = _("Move-in Pictures")
        form_kwargs["upload_instructions"] = _("Take pictures of these places in your apartment:")
        form_kwargs["upload_ideas"] = [
            _("Kitchen"),
            _("Kitchen appliances"),
            _("Bathroom walls"),
            _("Bathroom tub"),
            _("Living room"),
            _("Blinds/window coverings"),
            _("Anything that's damaged"),
        ]
        form_kwargs["max_images"] = settings.MAX_MOVE_IN_PICTURES_PER_UNIT
        form_kwargs["current_image_count"] = UnitImage.objects.for_user(
            self.request.user, unit=form_kwargs["unit"], image_type=MOVE_IN_PICTURE
        ).count()
        return form_kwargs


class UnitAddMoveOutPicturesFormView(UnitAddImagesFormViewBase):
    image_type = MOVE_OUT_PICTURE

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["label"] = _("Move-out Pictures")
        form_kwargs["upload_instructions"] = _("Take pictures of these places in your apartment:")
        form_kwargs["upload_ideas"] = [
            _("Kitchen"),
            _("Kitchen appliances"),
            _("Bathroom walls"),
            _("Bathroom tub"),
            _("Living room"),
            _("Blinds/window coverings"),
        ]
        form_kwargs["upload_instructions_footer"] = _(
            "Make sure you have good overall coverage of your unit in case your landlord claims damage."
        )
        form_kwargs["max_images"] = settings.MAX_MOVE_OUT_PICTURES_PER_UNIT
        form_kwargs["current_image_count"] = UnitImage.objects.for_user(
            self.request.user, unit=form_kwargs["unit"], image_type=MOVE_OUT_PICTURE
        ).count()
        return form_kwargs


@login_required
def sign_files(request, slug):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    )

    files = json.loads(request.body)["files"]

    existing_image_count = Unit.objects.get_for_user(request.user, slug=slug).unitimage_set.count()
    if (existing_image_count + len(files)) > (
        settings.MAX_DOCUMENTS_PER_UNIT + settings.MAX_MOVE_IN_PICTURES_PER_UNIT + settings.MAX_MOVE_OUT_PICTURES_PER_UNIT
    ):
        return HttpResponseBadRequest("Too many files.")

    resp = {}
    for f in files:
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
