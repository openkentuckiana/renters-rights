from django.test import TestCase
from hamcrest import assert_that, contains_string, equal_to, has_key

from documents.forms import DocumentForm, PhotosDocumentForm, SmallClaimsDocumentForm
from documents.models import DocumentField, DocumentTemplate
from noauth.models import User
from units.models import Unit


class DocumentFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.u = User.objects.create(is_active=True, username="eleanor@shellstrop.com")
        cls.unit = Unit.objects.create(
            unit_address_1="Unit address1",
            unit_address_2="Unit address 2",
            unit_city="Louisville",
            unit_state="KY",
            unit_zip_code="40201",
            owner=cls.u,
        )
        cls.unit2 = Unit.objects.create(
            unit_address_1="u", owner=User.objects.create(is_active=True, username="rando@example.com")
        )

        cls.dt = DocumentTemplate.objects.create(name="DT1", slug="dt-1", body="""This is {{field_1}} and {{field_2}}.""")
        cls.df1 = DocumentField.objects.create(name="field1", required=True, field_type=DocumentField.TEXT, document=cls.dt)
        cls.df2 = DocumentField.objects.create(name="field2", required=False, field_type=DocumentField.INTEGER, document=cls.dt)

    def test_form_requires_required_document_fields(self):
        form = DocumentForm(data={}, user=DocumentFormTests.u, document_template=DocumentFormTests.dt)
        self.assertFalse(form.is_valid())

        # Fields from base form
        assert_that(form.errors, has_key("sender_first_name"))
        assert_that(form.errors, has_key("sender_last_name"))
        assert_that(form.errors, has_key("unit"))
        assert_that(form.errors, has_key("sender_address_1"))

        # Required field from document template
        assert_that(form.errors, has_key("field1"))

    def test_form_requires_user_owned_unit(self):
        form = DocumentForm(
            data={"unit": DocumentFormTests.unit2.id}, user=DocumentFormTests.u, document_template=DocumentFormTests.dt
        )
        self.assertFalse(form.is_valid())
        assert_that(form.errors, has_key("unit"))
        assert_that(
            form.errors["unit"].as_text(),
            contains_string("Select a valid choice. That choice is not one of the available choices."),
        )

    def test_form_validates_document_field_types(self):
        form = DocumentForm(data={"field2": "NaN"}, user=DocumentFormTests.u, document_template=DocumentFormTests.dt)
        self.assertFalse(form.is_valid())
        assert_that(form.errors, has_key("field2"))
        assert_that(form.errors["field2"].as_text(), contains_string("Enter a whole number"))

    def test_form_works_with_required_document_fields(self):
        form = DocumentForm(
            data={
                "sender_first_name": "Eleanor",
                "sender_last_name": "Shellstrop",
                "sender_address_1": "123 Main",
                "sender_city": "Louisville",
                "sender_state": "KY",
                "sender_zip_code": "40202",
                "unit": DocumentFormTests.unit.id,
                "field1": "F1Value",
                "field2": 1,
            },
            user=DocumentFormTests.u,
            document_template=DocumentFormTests.dt,
        )
        self.assertTrue(form.is_valid())

    def test_use_unit_address_uses_unit_address_for_sender_info(self):
        form = DocumentForm(
            data={
                "sender_first_name": "Eleanor",
                "sender_last_name": "Shellstrop",
                "use_unit_address": True,
                "unit": DocumentFormTests.unit.id,
                "field1": "F1Value",
                "field2": 1,
            },
            user=DocumentFormTests.u,
            document_template=DocumentFormTests.dt,
        )
        self.assertTrue(form.is_valid())
        assert_that(form.cleaned_data["sender_address_1"], equal_to(DocumentFormTests.unit.unit_address_1))
        assert_that(form.cleaned_data["sender_address_2"], equal_to(DocumentFormTests.unit.unit_address_2))
        assert_that(form.cleaned_data["sender_city"], equal_to(DocumentFormTests.unit.unit_city))
        assert_that(form.cleaned_data["sender_state"], equal_to(DocumentFormTests.unit.unit_state))
        assert_that(form.cleaned_data["sender_zip_code"], equal_to(DocumentFormTests.unit.unit_zip_code))


class SmallClaimsDocumentFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.u = User.objects.create(is_active=True, username="eleanor@shellstrop.com")
        cls.unit = Unit.objects.create(unit_address_1="u", owner=cls.u)
        cls.unit2 = Unit.objects.create(
            unit_address_1="u", owner=User.objects.create(is_active=True, username="rando@example.com")
        )

    def test_form_requires_required_fields(self):
        form = SmallClaimsDocumentForm(data={}, user=SmallClaimsDocumentFormTests.u)
        self.assertFalse(form.is_valid())

        # Fields from base form
        assert_that(form.errors, has_key("sender_first_name"))
        assert_that(form.errors, has_key("sender_last_name"))
        assert_that(form.errors, has_key("unit"))
        assert_that(form.errors, has_key("sender_address_1"))

        # Required field from small claims form
        assert_that(form.errors, has_key("county"))
        assert_that(form.errors, has_key("claims_sum"))
        assert_that(form.errors, has_key("court_costs"))
        assert_that(form.errors, has_key("claims"))

    def test_form_requires_user_owned_unit(self):
        form = SmallClaimsDocumentForm(
            data={"unit": SmallClaimsDocumentFormTests.unit2.id}, user=SmallClaimsDocumentFormTests.u
        )
        self.assertFalse(form.is_valid())
        assert_that(form.errors, has_key("unit"))
        assert_that(
            form.errors["unit"].as_text(),
            contains_string("Select a valid choice. That choice is not one of the available choices."),
        )

    def test_form_validates_required_fields(self):
        form = SmallClaimsDocumentForm(
            data={"county": "Nope", "claims_sum": "NaN", "court_costs": "NaN"}, user=SmallClaimsDocumentFormTests.u
        )
        self.assertFalse(form.is_valid())
        assert_that(form.errors, has_key("county"))
        assert_that(form.errors["county"].as_text(), contains_string("Nope is not one of the available choices."))
        assert_that(form.errors, has_key("claims_sum"))
        assert_that(form.errors["claims_sum"].as_text(), contains_string("Enter a number"))
        assert_that(form.errors, has_key("court_costs"))
        assert_that(form.errors["court_costs"].as_text(), contains_string("Enter a number"))

    def test_form_works_with_required_document_fields(self):
        form = SmallClaimsDocumentForm(
            data={
                "sender_first_name": "Eleanor",
                "sender_last_name": "Shellstrop",
                "sender_address_1": "123 Main",
                "sender_city": "Louisville",
                "sender_state": "KY",
                "sender_zip_code": "40202",
                "unit": SmallClaimsDocumentFormTests.unit.id,
                "county": "Woodford",
                "claims_sum": 100,
                "court_costs": 100,
                "claims": "This is my claim.",
            },
            user=SmallClaimsDocumentFormTests.u,
        )
        self.assertTrue(form.is_valid())


class PhotosDocumentFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.u = User.objects.create(is_active=True, username="eleanor@shellstrop.com")
        cls.unit = Unit.objects.create(unit_address_1="u", owner=cls.u)
        cls.unit2 = Unit.objects.create(
            unit_address_1="u", owner=User.objects.create(is_active=True, username="rando@example.com")
        )

    def test_form_requires_required_fields(self):
        form = PhotosDocumentForm(data={}, user=PhotosDocumentFormTests.u)
        self.assertFalse(form.is_valid())

        # Fields from base form
        assert_that(form.errors, has_key("sender_first_name"))
        assert_that(form.errors, has_key("sender_last_name"))
        assert_that(form.errors, has_key("unit"))
        assert_that(form.errors, has_key("sender_address_1"))

    def test_form_requires_user_owned_unit(self):
        form = PhotosDocumentForm(data={"unit": PhotosDocumentFormTests.unit2.id}, user=PhotosDocumentFormTests.u)
        self.assertFalse(form.is_valid())
        assert_that(form.errors, has_key("unit"))
        assert_that(
            form.errors["unit"].as_text(),
            contains_string("Select a valid choice. That choice is not one of the available choices."),
        )

    def test_form_works_with_required_document_fields(self):
        form = PhotosDocumentForm(
            data={
                "sender_first_name": "Eleanor",
                "sender_last_name": "Shellstrop",
                "unit": PhotosDocumentFormTests.unit.id,
                "sender_address_1": "123 Main",
                "sender_city": "Louisville",
                "sender_state": "KY",
                "sender_zip_code": "40202",
            },
            user=PhotosDocumentFormTests.u,
        )
        self.assertTrue(form.is_valid())
