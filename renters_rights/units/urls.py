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
    sign_files,
)

urlpatterns = [
    path("", IndexView.as_view(), name="homepage"),
    path("units/", UnitListView.as_view(), name="unit-list"),
    path("unit/new/", UnitCreate.as_view(), name="unit-create"),
    path("unit/delete/<slug:slug>/", UnitDeleteView.as_view(), name="unit-delete"),
    path("unit/<slug:slug>/add-documents/", UnitAddDocumentsFormView.as_view(), name="unit-add-documents"),
    path("unit/<slug:slug>/add-move-in-pics/", UnitAddMoveInPicturesFormView.as_view(), name="unit-add-move-in-pictures"),
    path("unit/<slug:slug>/add-move-out-pics/", UnitAddMoveOutPicturesFormView.as_view(), name="unit-add-move-out-pictures"),
    path("unit/<slug:slug>/sign-files/", sign_files, name="sign-files"),
    path("unit/<slug:slug>/", UnitDetailView.as_view(), name="unit-detail"),
]
