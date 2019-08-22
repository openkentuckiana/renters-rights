from django.conf.urls import url
from django.urls import path

from .views import DocumentFormView, DocumentListView

app_name = "documents"
urlpatterns = [
    path("<int:id>/", DocumentFormView.as_view(), name="document-form"),
    url(r"", DocumentListView.as_view(), name="document-list"),
]
