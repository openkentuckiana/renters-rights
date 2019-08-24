from django.conf.urls import url

from .views import CodeView, LoginView

app_name = "noauth"
urlpatterns = [url(r"^code/$", CodeView.as_view(), name="code"), url(r"^log-in/$", LoginView.as_view(), name="log-in")]
