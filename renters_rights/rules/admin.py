from django.contrib import admin

from rules.models import Ordinance, Rule, RuleGroup


class OrdinanceAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("ordinance",)}


class RuleGroupAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}


class RuleAdmin(admin.ModelAdmin):
    list_display = ("__str__", "rule_group")


admin.site.register(Ordinance, OrdinanceAdmin)
admin.site.register(RuleGroup, RuleGroupAdmin)
admin.site.register(Rule, RuleAdmin)
