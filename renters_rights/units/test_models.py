import os
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.storage import default_storage
from django.test import TestCase, override_settings
from hamcrest import assert_that, equal_to, starts_with
from PIL import Image

from noauth.models import User

from .models import Item, UnitImage


class ItemModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.u = User.objects.create(is_active=True, district=cls.d, email="eleanor@shellstrop.com")

    def test_slug_generated(self):
        forty_five_character_name = "a" * 45
        i = Item.objects.create(name=forty_five_character_name, location=ItemModelTests.b, owner=ItemModelTests.u)
        assert_that(i.slug, starts_with(f"{forty_five_character_name}-"))

    def test_truncated_slug_generated(self):
        sixty_character_name = "a" * 60
        i = Item.objects.create(name=sixty_character_name, location=ItemModelTests.b, owner=ItemModelTests.u)
        assert_that(i.slug, starts_with(f"{sixty_character_name[:45]}-"))


class ItemImageModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.u = User.objects.create(is_active=True, district=cls.d, email="eleanor@shellstrop.com")
        cls.i = Item.objects.create(name="i", location=cls.b, owner=cls.u)

    @staticmethod
    def get_image_file(name="test.png", ext="png", size=(50, 50), color=(256, 0, 0)):
        file_obj = BytesIO()
        image = Image.new("RGBA", size=size, color=color)
        image.save(file_obj, ext)
        file_obj.seek(0)
        return File(file_obj, name=name)

    @override_settings(ITEM_IMAGE_MIN_HEIGHT_AND_WIDTH=50)
    def test_validate_image_height(self):
        with self.assertRaisesRegexp(
            ValidationError, "Images must be over 50 pixels tall and wide. Please upload a larger image."
        ):
            UnitImage.objects.create(image=self.get_image_file(size=(49, 500)), item=ItemImageModelTests.i)

    @override_settings(ITEM_IMAGE_MIN_HEIGHT_AND_WIDTH=50)
    def test_validate_image_width(self):
        with self.assertRaisesRegexp(
            ValidationError, "Images must be over 50 pixels tall and wide. Please upload a larger image."
        ):
            UnitImage.objects.create(image=self.get_image_file(size=(500, 49)), item=ItemImageModelTests.i)

    @override_settings(ITEM_IMAGE_MIN_HEIGHT_AND_WIDTH=10)
    @override_settings(ITEM_IMAGE_SIZES=[5, 10, 20])
    def test_validate_thumbnails_created(self):
        image = UnitImage.objects.create(image=self.get_image_file(size=(20, 20)), item=ItemImageModelTests.i)
        assert_that(default_storage.exists(image.image.path), equal_to(True))
        filename, extension = os.path.splitext(image.image.path)
        assert_that(default_storage.exists(f"{filename}-5{extension}"), equal_to(True))
        assert_that(default_storage.exists(f"{filename}-10{extension}"), equal_to(True))

    @override_settings(ITEM_IMAGE_MIN_HEIGHT_AND_WIDTH=10)
    @override_settings(ITEM_IMAGE_SIZES=[5, 10, 20])
    def test_image_downsized_if_larger_than_max_size(self):
        image = UnitImage.objects.create(image=self.get_image_file(size=(21, 21)), item=ItemImageModelTests.i)
        assert_that(default_storage.exists(image.image.path), equal_to(True))
        assert_that(image.image.height, equal_to(20))
        assert_that(image.image.width, equal_to(20))

    @override_settings(ITEM_IMAGE_MIN_HEIGHT_AND_WIDTH=10)
    @override_settings(ITEM_IMAGE_SIZES=[20])
    def test_image_not_downsized_if_not_larger_than_max_size(self):
        image = UnitImage.objects.create(image=self.get_image_file(size=(20, 20)), item=ItemImageModelTests.i)
        assert_that(default_storage.exists(image.image.path), equal_to(True))
        assert_that(image.image.height, equal_to(20))
        assert_that(image.image.width, equal_to(20))

    @override_settings(ITEM_IMAGE_MIN_HEIGHT_AND_WIDTH=10)
    @override_settings(ITEM_IMAGE_SIZES=[5, 10, 20])
    def test_images_are_cleaned_up_on_delete(self):
        image = UnitImage.objects.create(image=self.get_image_file(size=(21, 21)), item=ItemImageModelTests.i)
        assert_that(default_storage.exists(image.image.path), equal_to(True))
        filename, extension = os.path.splitext(image.image.path)
        assert_that(default_storage.exists(f"{filename}-5{extension}"), equal_to(True))
        assert_that(default_storage.exists(f"{filename}-10{extension}"), equal_to(True))

        image.delete()

        assert_that(default_storage.exists(image.image.path), equal_to(False))
        assert_that(default_storage.exists(f"{filename}-5{extension}"), equal_to(False))
        assert_that(default_storage.exists(f"{filename}-10{extension}"), equal_to(False))
