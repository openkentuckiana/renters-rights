import base64

from django.conf import settings
from django.http import HttpResponse


class BasicAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def unauthorized(self):
        response = HttpResponse("Unauthorized", status=401)
        response["WWW-Authenticate"] = f'Basic realm="{settings.SITE_NAME} App"'
        return response

    def __call__(self, request):
        if "HTTP_AUTHORIZATION" in request.META and (settings.BASIC_AUTH_USERNAME and settings.BASIC_AUTH_PASSWORD):
            authentication = request.META["HTTP_AUTHORIZATION"]
            (method, auth) = authentication.split(" ", 1)

            if method.upper() != "BASIC":
                return self.unauthorized()

            auth = base64.b64decode(auth.strip()).decode("utf-8")
            username, password = auth.split(":", 1)
            if username == settings.BASIC_AUTH_USERNAME and password == settings.BASIC_AUTH_PASSWORD:
                return self.get_response(request)

        return self.unauthorized()
