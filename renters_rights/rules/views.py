from itertools import groupby

from django.shortcuts import get_object_or_404, render
from django.views.generic import View

from rules.models import Rule


class IndexView(View):
    def get(self, request):
        return render(request, "index.html")


class GetHelpView(View):
    def get(self, request):
        return render(request, "get-help.html")


class RulesView(View):
    def get(self, request):
        return render(request, "rules.html", context={"rules": Rule.objects.all()})


class RuleView(View):
    def get(self, request, slug):
        return render(request, "rule.html", context={"rule": get_object_or_404(Rule, slug=slug)})
