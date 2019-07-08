from django.urls import path

from .views import (AnotherView, IndexView, UnitCreateFormView, UnitDetailView,
                    UnitListView)

urlpatterns = [
    path("", IndexView.as_view()),
    path("units/", UnitListView.as_view(), name="unit-list"),
    path("unit/new/", UnitCreateFormView.as_view()),
    path("unit/<slug:slug>/", UnitDetailView.as_view(), name="unit-detail"),
    path("another/", AnotherView.as_view()),
]
