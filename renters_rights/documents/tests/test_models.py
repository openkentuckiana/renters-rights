from django.test import TestCase
from hamcrest import assert_that, contains_inanyorder, equal_to, none

from documents.models import DocumentField, DocumentTemplate


class DocumentModelTests(TestCase):
    def setUp(self):
        self.doc_template_with_fields = DocumentTemplate.objects.create(name="My doc", slug="my-doc-slug")
        self.df1 = DocumentField.objects.create(
            name="Field1", required=False, field_type=DocumentField.DATE, document=self.doc_template_with_fields
        )
        self.df2 = DocumentField.objects.create(
            name="Field2", required=True, field_type=DocumentField.TEXT, document=self.doc_template_with_fields
        )
        self.doc_template_without_fields = DocumentTemplate.objects.create(
            name="My doc no fields", slug="my-doc-slug-no-fields"
        )

    def test_get_document_fields_returns_fields(self):
        assert_that(self.doc_template_with_fields.fields(), contains_inanyorder(self.df1, self.df2))

    def test_document_str_returns_name(self):
        assert_that(str(self.doc_template_with_fields), equal_to(self.doc_template_with_fields.name))

    def test_document_field_str_returns_name(self):
        assert_that(str(self.df1), equal_to(self.df1.name))
