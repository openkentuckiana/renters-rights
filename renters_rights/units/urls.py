from django.urls import path

from .views import IndexView, UnitCreate, UnitDetailView, UnitListView, sign_files

urlpatterns = [
    path("", IndexView.as_view(), name="homepage"),
    path("units/", UnitListView.as_view(), name="unit-list"),
    path("unit/new/", UnitCreate.as_view(), name="unit-create"),
    path("unit/new/sign-files/", sign_files, name="sign-files"),
    path("unit/<slug:slug>/", UnitDetailView.as_view(), name="unit-detail"),
]
