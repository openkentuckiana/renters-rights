from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.flatpages import views
from django.urls import include, path

admin.site.site_header = "Renter Haven Administration"

urlpatterns = [
    path("", include("units.urls")),
    path("admin/", admin.site.urls),
    path("auth/", include("noauth.urls")),
    path("letters-forms/", include("documents.urls")),
    path("<path:url>", views.flatpage),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    # Debug could be on when deployed, but we'd be using django-storages and a remote location for media storage
    if settings.MEDIA_URL and settings.MEDIA_ROOT:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
