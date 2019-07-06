from django.contrib import admin

from lib.admin import SoftDeleteModelAdmin

from .models import Item, UnitImage


class ItemImageAdmin(admin.ModelAdmin):
    readonly_fields = ("full_size_height", "full_size_width", "thumbnail_sizes")


admin.site.register(Item, SoftDeleteModelAdmin)
admin.site.register(UnitImage, ItemImageAdmin)
