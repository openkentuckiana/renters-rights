from unittest.mock import Mock

from django.http import HttpRequest, HttpResponse
from django.test import TestCase
from hamcrest import assert_that, equal_to, same_instance

from units.middleware import TurbolinksMiddleware


class TurbolinksMiddlewareTests(TestCase):
    def setUp(self):
        self.original_response = HttpResponse()
        get_response = Mock()
        get_response.return_value = self.original_response
        self.m = TurbolinksMiddleware(get_response)

    def test_original_response_returned_when_turbolinks_header_missing(self):
        request = HttpRequest()
        response = self.m(request)
        assert_that(response, same_instance(self.original_response))

    def test_response_includes_turbolinks_location_if_turbolinks_referrer_and_not_redirect(self):
        request = HttpRequest()
        request.session = {}
        request.META["HTTP_TURBOLINKS_REFERRER"] = True
        request.session["_turbolinks_redirect_to"] = "PAGE"

        response = self.m(request)
        assert_that(response["Turbolinks-Location"], equal_to("PAGE"))

    def test_session__turbolinks_redirect_to_set_if_turbolinks_referrer_and_redirect_and_prev_not_location_set(self):
        self.original_response["Location"] = ".new-page"

        request = HttpRequest()
        request.session = {}
        request.META["HTTP_TURBOLINKS_REFERRER"] = True

        response = self.m(request)
        assert_that(response, same_instance(self.original_response))
        assert_that(request.session["_turbolinks_redirect_to"], equal_to(".new-page"))

    def test_session__turbolinks_redirect_to_set_if_turbolinks_referrer_and_redirect_and_prev_location_set(self):
        self.original_response["Location"] = ".new-page"

        request = HttpRequest()
        request.session = {}
        request.META["HTTP_TURBOLINKS_REFERRER"] = True
        request.session["_turbolinks_redirect_to"] = "last-page"

        response = self.m(request)
        assert_that(response, same_instance(self.original_response))
        assert_that(request.session["_turbolinks_redirect_to"], equal_to("last-page.new-page"))
