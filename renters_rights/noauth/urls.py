from django.conf.urls import url

from .views import CodeView, LoginView

app_name = "noauth"
urlpatterns = [
    url(r"^code/$", CodeView.as_view(), name="code"),
    url(r"^login/$", LoginView.as_view(), name="login"),
]
