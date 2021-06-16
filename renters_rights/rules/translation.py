from modeltranslation.translator import TranslationOptions, translator

from rules.models import Ordinance, Rule


class OrdinanceTranslationOptions(TranslationOptions):
    fields = ("legal_description",)


class RuleTranslationOptions(TranslationOptions):
    fields = ("title", "plain_description")


translator.register(Rule, RuleTranslationOptions)
translator.register(Ordinance, OrdinanceTranslationOptions)
