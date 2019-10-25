from django.conf.urls import url

from .views import CodeView, LogInView, LogOutView, UserProfileView

app_name = "noauth"
urlpatterns = [
    url(r"^code/$", CodeView.as_view(), name="code"),
    url(r"^log-in/$", LogInView.as_view(), name="log-in"),
    url(r"^log-out/$", LogOutView.as_view(), name="log-out"),
    url(r"^details/$", UserProfileView.as_view(), name="account-details"),
]
