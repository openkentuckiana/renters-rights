from django.test import Client
from django.urls import reverse

from units.models import Unit, UnitImage
from units.tests import UnitBaseTestCase


class UnitViewTests(UnitBaseTestCase):
    def test_two_units(self):
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

    def test_one_unit(self):
        c = Client()
        c.force_login(UnitViewTests.u)
        response = c.get(reverse("unit-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, UnitViewTests.unit.unit_address_1)
        assert UnitViewTests.unit in response.context["unit_list"]

    def test_no_when_not_logged_in(self):
        response = self.client.get(reverse("unit-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No units.")
        self.assertQuerysetEqual(response.context["unit_list"], [])
