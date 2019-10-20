from django.urls import path

from .views import (
    IndexView,
    UnitAddDocumentsFormView,
    UnitAddMoveInPicturesFormView,
    UnitAddMoveOutPicturesFormView,
    UnitCreate,
    UnitDeleteView,
    UnitDetailView,
    UnitListView,
    UnitUpdate,
    sign_files,
)

urlpatterns = [
    path("", IndexView.as_view(), name="homepage"),
    path("units/", UnitListView.as_view(), name="unit-list"),
    path("units/new/", UnitCreate.as_view(), name="unit-create"),
    path("units/delete/<slug:slug>/", UnitDeleteView.as_view(), name="unit-delete"),
    path("units/edit/<slug:slug>/", UnitUpdate.as_view(), name="unit-edit"),
    path("units/<slug:slug>/add-documents/", UnitAddDocumentsFormView.as_view(), name="unit-add-documents"),
    path("units/<slug:slug>/add-move-in-pics/", UnitAddMoveInPicturesFormView.as_view(), name="unit-add-move-in-pictures"),
    path("units/<slug:slug>/add-move-out-pics/", UnitAddMoveOutPicturesFormView.as_view(), name="unit-add-move-out-pictures"),
    path("units/<slug:slug>/sign-files/", sign_files, name="sign-files"),
    path("units/<slug:slug>/", UnitDetailView.as_view(), name="unit-detail"),
]
