from unittest.mock import patch

from django.test import TransactionTestCase, override_settings
from django.utils.datastructures import MultiValueDict
from hamcrest import assert_that, contains, has_length

from noauth.models import User
from units.forms import UnitForm
from units.models import Unit
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


class UnitFormCreateImagesTests(TransactionTestCase):
    @patch("django.forms.ModelForm.save")
    @override_settings(UNIT_IMAGE_MIN_HEIGHT_AND_WIDTH=10)
    def test_unit_form_valid_two_documents(self, m_save):
        u = User.objects.create(is_active=True, username="eleanor2@shellstrop.com")
        unit = Unit.objects.create(unit_address_1="u", owner=u)
        m_save.return_value = unit
        i1 = UnitBaseTestCase.get_image_file()
        i2 = UnitBaseTestCase.get_image_file()
        form = UnitForm(data={"unit_address_1": "1"}, files=MultiValueDict({"documents": [i1, i2]}))
        instance = form.save()
        assert_that(instance.unitimage_set.all(), has_length(2))

    @patch("django.forms.ModelForm.save")
    @override_settings(UNIT_IMAGE_MIN_HEIGHT_AND_WIDTH=10)
    def test_unit_form_valid_two_pictures(self, m_save):
        u = User.objects.create(is_active=True, username="eleanor2@shellstrop.com")
        unit = Unit.objects.create(unit_address_1="u", owner=u)
        m_save.return_value = unit
        i1 = UnitBaseTestCase.get_image_file()
        i2 = UnitBaseTestCase.get_image_file()
        form = UnitForm(data={"unit_address_1": "1"}, files=MultiValueDict({"pictures": [i1, i2]}))
        instance = form.save()
        assert_that(instance.unitimage_set.all(), has_length(2))

    @patch("django.forms.ModelForm.save")
    @patch("boto3.client")
    @override_settings(UNIT_IMAGE_MIN_HEIGHT_AND_WIDTH=10)
    def test_unit_form_valid_two_images_s3(self, m_client, m_save):
        u = User.objects.create(is_active=True, username="eleanor2@shellstrop.com")
        unit = Unit.objects.create(unit_address_1="u", owner=u)
        m_save.return_value = unit

        i = UnitBaseTestCase.get_image_file()
        m_client.return_value.get_object.return_value = {"Body": i}

        form = UnitForm(data={"unit_address_1": "1", "s3_documents": "1"})
        instance = form.save()
        assert_that(instance.unitimage_set.all(), has_length(1))

    # TODO: Test that thumbnails are deleted if exception raised during save()
