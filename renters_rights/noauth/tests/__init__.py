from django.test import TestCase

from noauth.models import User


class UnitBaseTestCase(TestCase):
    u = None
    unit = None

    @classmethod
    def setUpTestData(cls):
        cls.u = User.objects.create(
            is_active=True,
            first_name="Eleanor",
            last_name="Shellstrop",
            username="eleanor@shellstrop.com",
            email="eleanor@shellstrop.com",
        )
