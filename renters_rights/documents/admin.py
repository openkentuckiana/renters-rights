from django.contrib import admin

from .models import DocumentField, DocumentTemplate


class DocumentFieldInline(admin.TabularInline):
    model = DocumentField


class DocumentAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    inlines = [DocumentFieldInline]


admin.site.register(DocumentTemplate, DocumentAdmin)
admin.site.register(DocumentField, admin.ModelAdmin)
