from django.utils.datastructures import MultiValueDict

from units.forms import UnitAddImageForm, UnitForm
from units.tests import UnitBaseTestCase


class UnitFormTests(UnitBaseTestCase):
    def test_unit_form_valid_no_images(self):
        form = UnitForm(data={"unit_address_1": "1"})
        self.assertTrue(form.is_valid())


class UnitAddImageFormTests(UnitBaseTestCase):
    def test_unit_form_invalid_too_many_images(self):
        form = UnitAddImageForm(
            unit=UnitBaseTestCase.unit,
            label="docs",
            max_images=2,
            current_image_count=0,
            files=MultiValueDict({"images": [1, 2, 3]}),
        )
        self.assertFalse(form.is_valid())

    def test_unit_form_invalid_too_many_images_with_current_images(self):
        form = UnitAddImageForm(
            unit=UnitBaseTestCase.unit, label="docs", max_images=2, current_image_count=2, files=MultiValueDict({"images": [1]})
        )
        self.assertFalse(form.is_valid())
