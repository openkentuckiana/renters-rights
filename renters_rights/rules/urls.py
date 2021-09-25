from django.urls import path

from .views import (
    GetHelpView,
    HowItWorksView,
    IndexView,
    ResourcesView,
    RulesView,
    RuleView,
)

urlpatterns = [
    path("", IndexView.as_view(), name="homepage"),
    path("how-it-works", HowItWorksView.as_view(), name="how-it-works"),
    path("get-help", GetHelpView.as_view(), name="get-help"),
    path("resources", ResourcesView.as_view(), name="resources"),
    path("rules", RulesView.as_view(), name="rules"),
    path("rules/<slug:slug>", RuleView.as_view(), name="rule"),
]
