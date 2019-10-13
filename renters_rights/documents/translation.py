from modeltranslation.translator import TranslationOptions, translator

from .models import DocumentField, DocumentTemplate


class DocumentTemplateTranslationOptions(TranslationOptions):
    fields = ("name", "description")


class DocumentFieldTranslationOptions(TranslationOptions):
    fields = ("name",)


translator.register(DocumentTemplate, DocumentTemplateTranslationOptions)
translator.register(DocumentField, DocumentFieldTranslationOptions)
