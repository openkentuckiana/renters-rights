import datetime
import os
from io import BytesIO

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.storage import default_storage
from django.test import TransactionTestCase, override_settings
from hamcrest import assert_that, equal_to, only_contains, starts_with
from PIL import Image

from noauth.models import User
from units.models import DOCUMENT, MOVE_IN_PICTURE, MOVE_OUT_PICTURE, Unit, UnitImage
from units.tests import UnitBaseTestCase


class UnitModelTests(UnitBaseTestCase):
    def test_str_repr(self):
        forty_five_character_name = "a" * 45
        u = Unit.objects.create(unit_address_1=forty_five_character_name, owner=UnitModelTests.u)
        assert_that(str(u), equal_to(forty_five_character_name))

    def test_slug_generated(self):
        forty_five_character_name = "a" * 45
        u = Unit.objects.create(unit_address_1=forty_five_character_name, owner=UnitModelTests.u)
        assert_that(u.slug, starts_with(f"{forty_five_character_name}-"))

    def test_truncated_slug_generated(self):
        sixty_character_name = "a" * 65
        u = Unit.objects.create(unit_address_1=sixty_character_name, owner=UnitModelTests.u)
        assert_that(u.slug, starts_with(f"{sixty_character_name[:45]}-"))

    @override_settings(UNIT_IMAGE_MIN_HEIGHT_AND_WIDTH=10)
    @override_settings(UNIT_IMAGE_MAX_HEIGHT_AND_WIDTH=20)
    @override_settings(UNIT_IMAGE_SIZES=[5, 10, 20])
    def test_pictures_returns_only_pictures(self):
        mi_picture = UnitImage.objects.create(
            image=self.get_image_file(size=(20, 20)),
            image_type=MOVE_IN_PICTURE,
            unit=UnitModelTests.unit,
            owner=UnitModelTests.u,
        )
        mo_picture = UnitImage.objects.create(
            image=self.get_image_file(size=(20, 20)),
            image_type=MOVE_OUT_PICTURE,
            unit=UnitModelTests.unit,
            owner=UnitModelTests.u,
        )
        document = UnitImage.objects.create(
            image=self.get_image_file(size=(20, 20)), image_type=DOCUMENT, unit=UnitModelTests.unit, owner=UnitModelTests.u
        )

        assert_that(UnitModelTests.unit.pictures(), only_contains(mi_picture, mo_picture))

    @override_settings(UNIT_IMAGE_MIN_HEIGHT_AND_WIDTH=10)
    @override_settings(UNIT_IMAGE_MAX_HEIGHT_AND_WIDTH=20)
    @override_settings(UNIT_IMAGE_SIZES=[5, 10, 20])
    def test_documents_returns_only_documents(self):
        mi_picture = UnitImage.objects.create(
            image=self.get_image_file(size=(20, 20)),
            image_type=MOVE_IN_PICTURE,
            unit=UnitModelTests.unit,
            owner=UnitModelTests.u,
        )
        mo_picture = UnitImage.objects.create(
            image=self.get_image_file(size=(20, 20)),
            image_type=MOVE_OUT_PICTURE,
            unit=UnitModelTests.unit,
            owner=UnitModelTests.u,
        )
        document = UnitImage.objects.create(
            image=self.get_image_file(size=(20, 20)), image_type=DOCUMENT, unit=UnitModelTests.unit, owner=UnitModelTests.u
        )

        assert_that(UnitModelTests.unit.documents(), only_contains(document))


class UnitImageModelTests(UnitBaseTestCase):
    @override_settings(UNIT_IMAGE_MIN_HEIGHT_AND_WIDTH=10)
    @override_settings(UNIT_IMAGE_MAX_HEIGHT_AND_WIDTH=20)
    @override_settings(UNIT_IMAGE_SIZES=[5, 10, 20])
    def test_str_repr(self):
        image = UnitImage.objects.create(
            image=self.get_image_file(size=(20, 20)), unit=UnitImageModelTests.unit, owner=UnitImageModelTests.u
        )
        assert_that(str(image), equal_to(image.image.name))

    @override_settings(UNIT_IMAGE_MIN_HEIGHT_AND_WIDTH=50)
    def test_validate_image_height(self):
        with self.assertRaisesRegexp(
            ValidationError, "Images must be over 50 pixels tall and wide. Please upload a larger image."
        ):
            UnitImage.objects.create(
                image=self.get_image_file(size=(49, 500)), unit=UnitImageModelTests.unit, owner=UnitImageModelTests.u
            )

    @override_settings(UNIT_IMAGE_MIN_HEIGHT_AND_WIDTH=50)
    def test_validate_image_width(self):
        with self.assertRaisesRegexp(
            ValidationError, "Images must be over 50 pixels tall and wide. Please upload a larger image."
        ):
            UnitImage.objects.create(
                image=self.get_image_file(size=(500, 49)), unit=UnitImageModelTests.unit, owner=UnitImageModelTests.u
            )

    @override_settings(UNIT_IMAGE_MIN_HEIGHT_AND_WIDTH=10)
    @override_settings(UNIT_IMAGE_MAX_HEIGHT_AND_WIDTH=20)
    @override_settings(UNIT_IMAGE_SIZES=[5, 10, 20])
    def test_validate_thumbnails_created(self):
        image = UnitImage.objects.create(
            image=self.get_image_file(size=(20, 20)), unit=UnitImageModelTests.unit, owner=UnitImageModelTests.u
        )
        assert_that(default_storage.exists(image.image.path), equal_to(True))
        filename, extension = os.path.splitext(image.image.path)
        assert_that(default_storage.exists(f"{filename}-5{extension}"), equal_to(True))
        assert_that(default_storage.exists(f"{filename}-10{extension}"), equal_to(True))

    @override_settings(UNIT_IMAGE_MIN_HEIGHT_AND_WIDTH=10)
    @override_settings(UNIT_IMAGE_MAX_HEIGHT_AND_WIDTH=20)
    @override_settings(UNIT_IMAGE_SIZES=[5, 10, 20])
    def test_validate_thumbnail_property(self):
        image = UnitImage.objects.create(
            image=self.get_image_file(size=(20, 20)), unit=UnitImageModelTests.unit, owner=UnitImageModelTests.u
        )
        assert_that(default_storage.exists(image.image.path), equal_to(True))
        assert_that(image.thumbnail, equal_to(settings.MEDIA_URL + image.image.name.replace(".jpg", "-5.jpg")))

    @override_settings(UNIT_IMAGE_MIN_HEIGHT_AND_WIDTH=10)
    @override_settings(UNIT_IMAGE_MAX_HEIGHT_AND_WIDTH=20)
    @override_settings(UNIT_IMAGE_SIZES=[5, 10, 20])
    def test_validate_thumbnail_internal_property(self):
        image = UnitImage.objects.create(
            image=self.get_image_file(size=(20, 20)), unit=UnitImageModelTests.unit, owner=UnitImageModelTests.u
        )
        assert_that(default_storage.exists(image.image.path), equal_to(True))
        assert_that(image.thumbnail_internal, equal_to(settings.MEDIA_URL + image.image.name.replace(".jpg", "-10.jpg")))

    @override_settings(UNIT_IMAGE_MIN_HEIGHT_AND_WIDTH=10)
    @override_settings(UNIT_IMAGE_MAX_HEIGHT_AND_WIDTH=20)
    @override_settings(UNIT_IMAGE_SIZES=[5, 10, 20])
    def test_image_downsized_if_larger_than_max_size(self):
        image = UnitImage.objects.create(
            image=self.get_image_file(size=(21, 21)), unit=UnitImageModelTests.unit, owner=UnitImageModelTests.u
        )
        assert_that(default_storage.exists(image.image.path), equal_to(True))
        assert_that(image.image.height, equal_to(20))
        assert_that(image.image.width, equal_to(20))

    @override_settings(UNIT_IMAGE_MIN_HEIGHT_AND_WIDTH=10)
    @override_settings(UNIT_IMAGE_MAX_HEIGHT_AND_WIDTH=20)
    @override_settings(UNIT_IMAGE_SIZES=[5, 10, 20])
    def test_image_not_downsized_if_not_larger_than_max_size(self):
        image = UnitImage.objects.create(
            image=self.get_image_file(size=(20, 20)), unit=UnitImageModelTests.unit, owner=UnitImageModelTests.u
        )
        assert_that(default_storage.exists(image.image.path), equal_to(True))
        assert_that(image.image.height, equal_to(20))
        assert_that(image.image.width, equal_to(20))

    @override_settings(UNIT_IMAGE_MIN_HEIGHT_AND_WIDTH=10)
    @override_settings(UNIT_IMAGE_MAX_HEIGHT_AND_WIDTH=20)
    @override_settings(UNIT_IMAGE_SIZES=[5, 10, 20])
    def test_images_are_cleaned_up_on_delete(self):
        image = UnitImage.objects.create(
            image=self.get_image_file(size=(21, 21)), unit=UnitImageModelTests.unit, owner=UnitImageModelTests.u
        )
        assert_that(default_storage.exists(image.image.path), equal_to(True))
        filename, extension = os.path.splitext(image.image.path)
        assert_that(default_storage.exists(f"{filename}-5{extension}"), equal_to(True))
        assert_that(default_storage.exists(f"{filename}-10{extension}"), equal_to(True))

        image.delete()

        assert_that(default_storage.exists(image.image.path), equal_to(False))
        assert_that(default_storage.exists(f"{filename}-5{extension}"), equal_to(False))
        assert_that(default_storage.exists(f"{filename}-10{extension}"), equal_to(False))
