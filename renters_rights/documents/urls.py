from django.conf.urls import url
from django.urls import path

from .views import DocumentFormView, DocumentListView, PhotosDocumentFormView, SmallClaimsDocumentFormView

app_name = "documents"
urlpatterns = [
    url(r"^$", DocumentListView.as_view(), name="document-list"),
    path("<int:id>/", DocumentFormView.as_view(), name="document-form"),
    path("photos/", PhotosDocumentFormView.as_view(), name="photos-document-form"),
    path("small-claims/", SmallClaimsDocumentFormView.as_view(), name="small-claims-document-form"),
]
