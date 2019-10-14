import io
import os
import tempfile

import pdfrw
from django.conf import settings
from django.http import HttpResponse
from django.template import Context, Template
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, ListView
from weasyprint import HTML

from documents.forms import DocumentForm, PhotosDocumentForm, SmallClaimsDocumentForm
from documents.models import DocumentTemplate
from lib.views import ProtectedView

ANNOT_KEY = "/Annots"
ANNOT_FIELD_KEY = "/T"
ANNOT_VAL_KEY = "/V"
ANNOT_RECT_KEY = "/Rect"
SUBTYPE_KEY = "/Subtype"
WIDGET_SUBTYPE_KEY = "/Widget"


class DocumentListView(ListView):
    model = DocumentTemplate
    context_object_name = "document_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model"] = self.model
        return context

    def get_queryset(self):
        return DocumentTemplate.objects.all()


class DocumentFormView(FormView, ProtectedView):
    template_name = "documents/document_form.html"
    form_class = DocumentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_name"] = DocumentTemplate.objects.get(id=self.kwargs["id"]).name
        return context

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["document_template"] = DocumentTemplate.objects.get(id=self.kwargs["id"])
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def form_valid(self, form):
        document_template = DocumentTemplate.objects.get(id=self.kwargs["id"])

        body = Template(document_template.body).render(Context(form.cleaned_data))
        context = {**form.cleaned_data, **{"body": body, "user": self.request.user}}
        pdf_html = render_to_string("basic_letter.html", context)

        pdf = io.BytesIO()
        HTML(string=pdf_html).write_pdf(pdf)

        response = HttpResponse(pdf.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename={document_template.file_name}.pdf"
        return response


class PhotosDocumentFormView(FormView, ProtectedView):
    template_name = "documents/document_form.html"
    form_class = PhotosDocumentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_name"] = _("Date-verified Photo Report")
        return context

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def form_valid(self, form):
        context = {
            **form.cleaned_data,
            **{"user": self.request.user, "site_name": settings.SITE_NAME, "site_url": self.request.build_absolute_uri("/")},
        }
        pdf_html = render_to_string("photo_report.html", context)

        pdf = io.BytesIO()
        HTML(string=pdf_html).write_pdf(pdf)

        response = HttpResponse(pdf.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = "attachment; filename=PhotoReport.pdf"
        return response


class SmallClaimsDocumentFormView(FormView, ProtectedView):
    template_name = "documents/document_form.html"
    form_class = SmallClaimsDocumentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_name"] = _("Small Claims Court Form")
        return context

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def form_valid(self, form):
        template_pdf = pdfrw.PdfReader(os.path.abspath(os.path.join(os.path.dirname(__file__), "templates/AOC-175.pdf")))

        plaintiff_name = (
            f"{self.request.user.first_name} {self.request.user.first_name}"
            if (self.request.user.first_name and self.request.user.first_name)
            else f"{form.cleaned_data['sender_first_name']} {form.cleaned_data['sender_last_name']}"
        )

        data_dict = {
            "county": form.cleaned_data["county"],
            "plaintiff_full_name": plaintiff_name,
            "plaintiff_full_name_2": plaintiff_name,
            "plaintiff_address_1": form.cleaned_data["sender_address_1"],
            "plaintiff_address_2": form.cleaned_data["sender_address_2"],
            "plaintiff_city_state_zip": f"{form.cleaned_data['sender_city']}, {form.cleaned_data['sender_state']} {form.cleaned_data['sender_zip_code']}",
            "defendant_full_name": form.cleaned_data["unit"].landlord_name,
            "defendant_address_1": form.cleaned_data["unit"].landlord_address_1,
            "defendant_address_2": form.cleaned_data["unit"].landlord_address_2,
            "defendant_city_state_zip": f"{form.cleaned_data['unit'].landlord_city}, {form.cleaned_data['unit'].landlord_state} {form.cleaned_data['unit'].landlord_zip_code}",
            "claims_sum": "${0:.2f}".format(form.cleaned_data["claims_sum"]),
            "court_costs": "${0:.2f}".format(form.cleaned_data["court_costs"]),
            "claims": form.cleaned_data["claims"],
        }

        if form.cleaned_data["is_landlord_company"]:
            data_dict["defendant_company"] = "X"
        else:
            data_dict["defendant_individual"] = "X"

        for page in template_pdf.pages:
            annotations = page[ANNOT_KEY]
            for annotation in annotations:
                if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY:
                    if annotation[ANNOT_FIELD_KEY]:
                        key = annotation[ANNOT_FIELD_KEY][1:-1]
                        if key in data_dict.keys():
                            annotation.update(pdfrw.PdfDict(V="{}".format(data_dict[key])))

        template_pdf.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject("true")))
        with tempfile.TemporaryFile() as fp:
            pdfrw.PdfWriter().write(fp, template_pdf)

            fp.seek(0)

            response = HttpResponse(fp.read(), content_type="application/pdf")
            response["Content-Disposition"] = "attachment; filename=SmallClaims.pdf"
            return response
