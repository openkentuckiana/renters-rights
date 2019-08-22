from modeltranslation.translator import TranslationOptions, translator

from .models import DocumentField


class DocumentFieldTranslationOptions(TranslationOptions):
    fields = ("name",)


translator.register(DocumentField, DocumentFieldTranslationOptions)
