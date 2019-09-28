from io import BytesIO

import PyPDF2
from django.test import Client, TestCase
from django.urls import reverse
from hamcrest import assert_that, contains_string, equal_to

from documents.models import DocumentField, DocumentTemplate
from documents.tests import UnitBaseTestCase
from noauth.models import User
from units.models import MOVE_IN_PICTURE, Unit, UnitImage


class DocumentListViewTests(TestCase):
    view_url = reverse("documents:document-list")

    def test_all_documents_are_shown(self):
        dt1 = DocumentTemplate.objects.create(name="DT1", slug="dt-1", body="""This is {{field_1}} and {{field_2}}.""")
        dt2 = DocumentTemplate.objects.create(name="DT2", slug="dt-2", body="""This is {{field_1}} and {{field_2}}.""")

        response = self.client.get(self.view_url)
        self.assertContains(response, dt1.name)
        self.assertContains(response, dt2.name)


class DocumentFormViewTests(UnitBaseTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.unit2 = Unit.objects.create(
            unit_address_1="Randos House", owner=User.objects.create(is_active=True, username="rando@example.com")
        )

        cls.dt = DocumentTemplate.objects.create(name="DT1", slug="dt-1", body="""This is {{field_1}} and {{field_2}}.""")
        cls.df1 = DocumentField.objects.create(name="field_1", required=True, field_type=DocumentField.TEXT, document=cls.dt)
        cls.df2 = DocumentField.objects.create(
            name="field_2", required=False, field_type=DocumentField.INTEGER, document=cls.dt
        )

    def test_document_form_rendered_with_fields(self):
        c = Client()
        c.force_login(DocumentFormViewTests.u)
        response = c.post(reverse("documents:document-form", args=(DocumentFormViewTests.dt.id,)))
        self.assertContains(response, DocumentFormViewTests.df1.name)
        self.assertContains(response, DocumentFormViewTests.df2.name)

    def test_document_form_rendered_with_users_unit(self):
        c = Client()
        c.force_login(DocumentFormViewTests.u)
        response = c.post(reverse("documents:document-form", args=(DocumentFormViewTests.dt.id,)))
        self.assertContains(response, str(DocumentFormViewTests.unit))
        self.assertNotContains(response, str(DocumentFormViewTests.unit2))

    def test_pdf(self):
        c = Client()
        c.force_login(DocumentFormViewTests.u)
        response = c.post(
            reverse("documents:document-form", args=(DocumentFormViewTests.dt.id,)),
            {
                "sender_first_name": "FirstName",
                "sender_last_name": "LastName",
                "unit": DocumentFormViewTests.unit.id,
                "use_unit_address": True,
                "field_1": "F1V",
                "field_2": 100,
            },
        )
        pdf_reader = PyPDF2.PdfFileReader(BytesIO(response.content), strict=False)
        page_content = pdf_reader.getPage(0).extractText()
        assert_that(page_content, contains_string("FirstName"))
        assert_that(page_content, contains_string("LastName"))
        assert_that(page_content, contains_string("This is F1V and 100."))


class PhotosDocumentFormViewTests(UnitBaseTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.u_img1 = UnitImage.objects.create(
            image=cls.get_image_file(size=(200, 200)), image_type=MOVE_IN_PICTURE, unit=cls.unit, owner=cls.u
        )
        cls.unit2 = Unit.objects.create(
            unit_address_1="Randos House", owner=User.objects.create(is_active=True, username="rando@example.com")
        )

    def test_document_form_rendered_with_users_unit(self):
        c = Client()
        c.force_login(PhotosDocumentFormViewTests.u)
        response = c.post(reverse("documents:photos-document-form"))
        self.assertContains(response, str(PhotosDocumentFormViewTests.unit))
        self.assertNotContains(response, str(PhotosDocumentFormViewTests.unit2))

    def test_pdf(self):
        c = Client()
        c.force_login(PhotosDocumentFormViewTests.u)
        response = c.post(
            reverse("documents:photos-document-form"),
            {
                "sender_first_name": "FirstName",
                "sender_last_name": "LastName",
                "unit": PhotosDocumentFormViewTests.unit.id,
                "use_unit_address": True,
            },
        )
        pdf_reader = PyPDF2.PdfFileReader(BytesIO(response.content), strict=False)
        page_content = pdf_reader.getPage(0).extractText()
        assert_that(page_content, contains_string("FirstName"))
        assert_that(page_content, contains_string("LastName"))
        assert_that(page_content, contains_string("Image uploaded at"))


class SmallClaimsDocumentFormViewTests(UnitBaseTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.u_img1 = UnitImage.objects.create(
            image=cls.get_image_file(size=(200, 200)), image_type=MOVE_IN_PICTURE, unit=cls.unit, owner=cls.u
        )
        cls.unit2 = Unit.objects.create(
            unit_address_1="Randos House", owner=User.objects.create(is_active=True, username="rando@example.com")
        )

    def test_document_form_rendered_with_users_unit(self):
        c = Client()
        c.force_login(SmallClaimsDocumentFormViewTests.u)
        response = c.post(reverse("documents:small-claims-document-form"))
        self.assertContains(response, str(SmallClaimsDocumentFormViewTests.unit))
        self.assertNotContains(response, str(SmallClaimsDocumentFormViewTests.unit2))

    def test_pdf(self):
        c = Client()
        c.force_login(SmallClaimsDocumentFormViewTests.u)
        response = c.post(
            reverse("documents:small-claims-document-form"),
            {
                "sender_first_name": "FirstName",
                "sender_last_name": "LastName",
                "unit": SmallClaimsDocumentFormViewTests.unit.id,
                "use_unit_address": True,
                "county": "Woodford",
                "claims_sum": 1500,
                "court_costs": 99.99,
                "claims": "These are my claims!",
            },
        )
        pdf_reader = PyPDF2.PdfFileReader(BytesIO(response.content), strict=False)
        fields = pdf_reader.getFormTextFields()
        assert_that(fields["county"], equal_to("Woodford"))
        assert_that(fields["plaintiff_address_1"], equal_to("Eleanors House"))
        assert_that(fields["plaintiff_full_name"], equal_to("FirstName LastName"))
        assert_that(fields["claims"], equal_to("These are my claims!"))
        assert_that(fields["claims_sum"], equal_to("$1500.00"))
        assert_that(fields["court_costs"], equal_to("$99.99"))
        assert_that(fields["defendant_individual"], equal_to("X"))
        assert_that(fields["defendant_company"], equal_to(None))
        assert_that(fields["plaintiff_full_name_2"], equal_to("FirstName LastName"))
