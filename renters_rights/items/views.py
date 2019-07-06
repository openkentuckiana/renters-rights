from django.shortcuts import render
from django.views.generic import FormView, View

from items.forms import ItemForm


class IndexView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return render(request, "index-logged-out.html")

        return render(request, "index.html")


class ItemFormView(FormView):
    template_name = "login.html"
    form_class = ItemForm
    success_url = "/"
