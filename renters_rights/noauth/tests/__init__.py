from django.test import TestCase

from noauth.models import User


class UnitBaseTestCase(TestCase):
    u = None
    unit = None

    @classmethod
    def setUpTestData(cls):
        cls.u = User.objects.create(is_active=True, username="eleanor@shellstrop.com")
