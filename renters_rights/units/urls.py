from django.urls import path

from .views import AnotherView, IndexView, UnitFormView

urlpatterns = [
    path("", IndexView.as_view()),
    path("unit/new/", UnitFormView.as_view()),
    path("another/", AnotherView.as_view()),
]
