from django.urls import path

from .views import GetHelpView, IndexView, RulesView, RuleView

urlpatterns = [
    path("", IndexView.as_view(), name="homepage"),
    path("get-help", GetHelpView.as_view(), name="get-help"),
    path("rules", RulesView.as_view(), name="rules"),
    path("rules/<slug:slug>", RuleView.as_view(), name="rule"),
]
