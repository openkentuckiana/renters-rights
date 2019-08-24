import json
from unittest.mock import patch

from django.test import Client
from django.urls import reverse
from freezegun import freeze_time

from noauth.models import User
from units.models import Unit, UnitImage
from units.tests import UnitBaseTestCase


class UnitViewTests(UnitBaseTestCase):
    def test_index_view_logged_out(self):
        response = self.client.get(reverse("homepage"))
        self.assertTemplateUsed(response, "index-logged-out.html")

    def test_index_view_logged_in(self):
        c = Client()
        c.force_login(UnitViewTests.u)
        response = c.get(reverse("homepage"))
        self.assertTemplateUsed(response, "index.html")

    def test_list_view_no_units_returned_when_not_logged_in(self):
        response = self.client.get(reverse("unit-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No units.")
        self.assertQuerysetEqual(response.context["unit_list"], [])

    def test_list_view_returns_a_signed_in_users_units_one_unit(self):
        c = Client()
        c.force_login(UnitViewTests.u)
        response = c.get(reverse("unit-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, UnitViewTests.unit.unit_address_1)
        assert UnitViewTests.unit in response.context["unit_list"]

    def test_list_view_returns_a_signed_in_users_units_two_units(self):
        unit2 = Unit.objects.create(unit_address_1="u2", owner=UnitViewTests.u)
        i1 = UnitImage.objects.create(image=self.get_image_file(size=(200, 200)), unit=unit2, owner=UnitViewTests.u)
        i2 = UnitImage.objects.create(image=self.get_image_file(size=(200, 200)), unit=unit2, owner=UnitViewTests.u)

        c = Client()
        c.force_login(UnitViewTests.u)
        response = c.get(reverse("unit-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, i1.thumbnail)
        self.assertContains(response, i2.thumbnail)
        self.assertContains(response, UnitViewTests.unit.unit_address_1)
        self.assertContains(response, unit2.unit_address_1)
        assert UnitViewTests.unit in response.context["unit_list"]
        assert unit2 in response.context["unit_list"]

    def test_list_view_does_not_return_another_users_units(self):
        other_user = User.objects.create(is_active=True, username="tahani@al-jamil.com")
        other_user_unit = Unit.objects.create(unit_address_1="other", owner=other_user)

        c = Client()
        c.force_login(UnitViewTests.u)
        response = c.get(reverse("unit-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, UnitViewTests.unit.unit_address_1)
        assert UnitViewTests.unit in response.context["unit_list"]
        assert other_user_unit not in response.context["unit_list"]

    def test_detail_view_requires_login(self):
        view_url = reverse("unit-detail", args=[self.unit.slug])
        response = self.client.get(view_url)
        self.assertRedirects(response, f"{reverse('noauth:log-in')}?next={view_url}")

    def test_detail_view_returns_expected_unit(self):
        c = Client()
        c.force_login(UnitViewTests.u)
        response = c.get(reverse("unit-detail", args=[self.unit.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, UnitViewTests.unit.unit_address_1)

    def test_create_view_requires_login(self):
        view_url = reverse("unit-create")
        response = self.client.get(view_url)
        self.assertRedirects(response, f"{reverse('noauth:log-in')}?next={view_url}")

    def test_create_view_creates_and_redirects_to_expected_url(self):
        c = Client()
        c.force_login(UnitViewTests.u)
        response = c.post(reverse("unit-create"), {"unit_address_1": "my_address"})
        self.assertRedirects(response, reverse("unit-list"))

    def test_create_view_creates_and_redirects_to_expected_url(self):
        c = Client()
        c.force_login(UnitViewTests.u)
        response = c.post(reverse("unit-create"), {"unit_address_1": "my_address"})
        self.assertRedirects(response, reverse("unit-list"))
        assert Unit.objects.get(unit_address_1="my_address") is not None

    @freeze_time("2000-01-01")
    def test_sign_files(self):
        c = Client()
        c.force_login(UnitViewTests.u)
        response = c.post(
            reverse("sign-files"), json.dumps({"files": ["file1.jpg", "file2.jpg"]}), content_type="application/json"
        )
        self.assertJSONEqual(
            str(response.content, encoding="utf8"),
            {
                "file1.jpg": {
                    "url": "https://renters-rights-uploads-test.s3.amazonaws.com/",
                    "fields": {
                        "acl": "private",
                        "Content-Type": "image/png",
                        "key": "eleanor@shellstrop.com/file1.jpg",
                        "AWSAccessKeyId": "INVALID",
                        "policy": "eyJleHBpcmF0aW9uIjogIjIwMDAtMDEtMDFUMDE6MDA6MDBaIiwgImNvbmRpdGlvbnMiOiBbeyJhY2wiOiAicHJpdmF0ZSJ9LCB7IkNvbnRlbnQtVHlwZSI6ICJpbWFnZS9wbmcifSwgWyJjb250ZW50LWxlbmd0aC1yYW5nZSIsIDUwMDAsIDE1MDAwMDAwXSwgeyJidWNrZXQiOiAicmVudGVycy1yaWdodHMtdXBsb2Fkcy10ZXN0In0sIHsia2V5IjogImVsZWFub3JAc2hlbGxzdHJvcC5jb20vZmlsZTEuanBnIn1dfQ==",
                        "signature": "i1HURmd5vT8qSQ6pWrE7MkxhteA=",
                    },
                },
                "file2.jpg": {
                    "url": "https://renters-rights-uploads-test.s3.amazonaws.com/",
                    "fields": {
                        "acl": "private",
                        "Content-Type": "image/png",
                        "key": "eleanor@shellstrop.com/file2.jpg",
                        "AWSAccessKeyId": "INVALID",
                        "policy": "eyJleHBpcmF0aW9uIjogIjIwMDAtMDEtMDFUMDE6MDA6MDBaIiwgImNvbmRpdGlvbnMiOiBbeyJhY2wiOiAicHJpdmF0ZSJ9LCB7IkNvbnRlbnQtVHlwZSI6ICJpbWFnZS9wbmcifSwgWyJjb250ZW50LWxlbmd0aC1yYW5nZSIsIDUwMDAsIDE1MDAwMDAwXSwgeyJidWNrZXQiOiAicmVudGVycy1yaWdodHMtdXBsb2Fkcy10ZXN0In0sIHsia2V5IjogImVsZWFub3JAc2hlbGxzdHJvcC5jb20vZmlsZTIuanBnIn1dfQ==",
                        "signature": "CQmgOFWj8WCawFd1JkUH3A7gcOs=",
                    },
                },
            },
        )
