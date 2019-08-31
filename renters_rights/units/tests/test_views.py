import json
from io import BytesIO
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files import File
from django.test import Client, TransactionTestCase, override_settings
from django.urls import reverse
from freezegun import freeze_time
from hamcrest import assert_that, contains, contains_inanyorder, equal_to, has_length, not_, not_none
from PIL import Image

from noauth.models import User
from units.models import MOVE_IN_PICTURE, Unit, UnitImage
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
        assert_that(response.context["unit_list"], contains(UnitViewTests.unit))

    def test_list_view_returns_a_signed_in_users_units_two_units(self):
        unit2 = Unit.objects.create(unit_address_1="u2", owner=UnitViewTests.u)
        i1 = UnitImage.objects.create(
            image=self.get_image_file(size=(200, 200)), image_type=MOVE_IN_PICTURE, unit=unit2, owner=UnitViewTests.u
        )
        i2 = UnitImage.objects.create(
            image=self.get_image_file(size=(200, 200)), image_type=MOVE_IN_PICTURE, unit=unit2, owner=UnitViewTests.u
        )

        c = Client()
        c.force_login(UnitViewTests.u)
        response = c.get(reverse("unit-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, i1.thumbnail)
        self.assertContains(response, i2.thumbnail)
        self.assertContains(response, UnitViewTests.unit.unit_address_1)
        self.assertContains(response, unit2.unit_address_1)
        assert_that(response.context["unit_list"], contains_inanyorder(UnitViewTests.unit, unit2))

    def test_list_view_does_not_return_another_users_units(self):
        other_user = User.objects.create(is_active=True, username="tahani@al-jamil.com")
        other_user_unit = Unit.objects.create(unit_address_1="other", owner=other_user)

        c = Client()
        c.force_login(UnitViewTests.u)
        response = c.get(reverse("unit-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, UnitViewTests.unit.unit_address_1)
        assert_that(response.context["unit_list"], contains(UnitViewTests.unit))
        assert_that(response.context["unit_list"], not_(contains(other_user_unit)))

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
        assert_that(Unit.objects.get(unit_address_1="my_address"), not_none())

    @freeze_time("2000-01-01")
    def test_sign_files(self):
        c = Client()
        c.force_login(UnitViewTests.u)
        response = c.post(
            reverse("sign-files", args=[UnitViewTests.unit.slug]),
            json.dumps({"files": ["file1.jpg", "file2.jpg"]}),
            content_type="application/json",
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

    @override_settings(MAX_DOCUMENTS_PER_UNIT=1)
    @override_settings(MAX_MOVE_IN_PICTURES_PER_UNIT=1)
    @override_settings(MAX_MOVE_OUT_PICTURES_PER_UNIT=1)
    @patch("django.db.models.query.QuerySet.count")
    def test_sign_files_returns_400_if_over_total_file_limit(self, m_count):
        m_count.return_value = 3

        c = Client()
        c.force_login(UnitViewTests.u)
        response = c.post(
            reverse("sign-files", args=[UnitViewTests.unit.slug]),
            json.dumps({"files": ["file1.jpg"]}),
            content_type="application/json",
        )
        assert_that(response.status_code, equal_to(400))


class UnitAddDocumentsFormViewTests(TransactionTestCase):
    @staticmethod
    def get_image_file(name="test.png", ext="png", size=(50, 50), color=(256, 0, 0)):
        file_obj = BytesIO()
        image = Image.new("RGBA", size=size, color=color)
        image.save(file_obj, ext)
        file_obj.seek(0)
        return File(file_obj, name=name)

    @override_settings(UNIT_IMAGE_MIN_HEIGHT_AND_WIDTH=10)
    @override_settings(UNIT_IMAGE_MAX_HEIGHT_AND_WIDTH=20)
    @override_settings(UNIT_IMAGE_SIZES=[5, 10, 20])
    def test_unit_form_valid_two_documents(self):
        u = User.objects.create(is_active=True, username="eleanor@shellstrop.com")
        unit = Unit.objects.create(unit_address_1="u", owner=u)

        c = Client()
        c.force_login(u)

        i1 = UnitBaseTestCase.get_image_file()
        i2 = UnitBaseTestCase.get_image_file()

        response = c.post(reverse("unit-add-documents", args=[unit.slug]), {"images": [i1, i2]})
        self.assertRedirects(response, reverse("unit-list"))
        unit.refresh_from_db()
        assert_that(unit.unitimage_set.all(), has_length(2))
