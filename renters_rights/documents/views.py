import io

from django.http import HttpResponse
from django.template import Context, Template
from django.template.loader import render_to_string
from django.views.generic import FormView, ListView
from weasyprint import HTML

from documents.forms import DocumentForm
from documents.models import DocumentTemplate
from lib.views import ProtectedView


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
    success_url = "/documents/"

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["document_template"] = DocumentTemplate.objects.get(id=self.kwargs["id"])
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def form_valid(self, form):
        document_template = DocumentTemplate.objects.get(id=self.kwargs["id"])

        body = Template(document_template.body).render(Context(form.cleaned_data))
        context = {**form.cleaned_data, **{"body": body, "user": self.request.user}}
        pdf_html = render_to_string("letter_base.html", context)

        pdf = io.BytesIO()
        HTML(string=pdf_html).write_pdf(pdf)

        response = HttpResponse(pdf.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = "attachment; filename=doc.pdf"
        return response
