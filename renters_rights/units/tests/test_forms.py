import datetime
import io
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.test import override_settings
from django.utils.datastructures import MultiValueDict
from hamcrest import assert_that, equal_to, starts_with

from units.forms import UnitForm
from units.models import Unit, UnitImage
from units.tests import UnitBaseTestCase


class UnitFormTests(UnitBaseTestCase):
    def test_unit_form_valid_no_images(self):
        form = UnitForm(data={"unit_address_1": "1"})
        self.assertTrue(form.is_valid())

    @override_settings(MAX_DOCUMENTS_PER_UNIT=2)
    def test_unit_form_invalid_too_many_documents(self):

        form = UnitForm(data={"unit_address_1": "1"}, files=MultiValueDict({"documents": [1, 2, 3]}))
        self.assertFalse(form.is_valid())

    @override_settings(MAX_DOCUMENTS_PER_UNIT=2)
    def test_unit_form_invalid_too_many_s3_documents(self):

        form = UnitForm(data={"unit_address_1": "1", "s3_documents": "1, 2, 3"})
        self.assertFalse(form.is_valid())

    @override_settings(MAX_PICTURES_PER_UNIT=2)
    def test_unit_form_invalid_too_many_pictures(self):
        form = UnitForm(data={"unit_address_1": "1"}, files=MultiValueDict({"pictures": [1, 2, 3]}))
        self.assertFalse(form.is_valid())

    @override_settings(MAX_PICTURES_PER_UNIT=2)
    def test_unit_form_invalid_too_many_s3_pictures(self):
        form = UnitForm(data={"unit_address_1": "1", "s3_pictures": "1, 2, 3"})
        self.assertFalse(form.is_valid())
