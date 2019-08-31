from unittest import TestCase

from django.db.models import CharField, Model
from hamcrest import assert_that, equal_to

from units.templatetags.bound_field import bound_field
from units.templatetags.model_strings import field_name


class TemplateTagTests(TestCase):
    def test_bound_field(self):
        field = bound_field({"thing": "value"}, "thing")
        assert_that(field, equal_to("value"))

    def test_field_name(self):
        class MyThing(Model):
            long_name = CharField(verbose_name="Long Name")

        assert_that(field_name(MyThing(), "long_name"), equal_to("Long Name"))
