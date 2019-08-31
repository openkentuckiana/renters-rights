from io import BytesIO

from django.core.files import File
from django.test import TestCase
from PIL import Image

from noauth.models import User
from units.models import Unit


class UnitBaseTestCase(TestCase):
    u = None
    unit = None

    @classmethod
    def setUpTestData(cls):
        cls.u = User.objects.create(is_active=True, username="eleanor@shellstrop.com")
        cls.unit = Unit.objects.create(unit_address_1="u", owner=cls.u)

    @staticmethod
    def get_image_file(name="test.png", ext="png", size=(50, 50), color=(256, 0, 0)):
        file_obj = BytesIO()
        image = Image.new("RGBA", size=size, color=color)
        image.save(file_obj, ext)
        file_obj.seek(0)
        return File(file_obj, name=name)
