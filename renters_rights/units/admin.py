from django.contrib import admin

from .models import Unit, UnitImage


class UnitAdmin(admin.ModelAdmin):
    list_display = ("unit_address_1", "owner")
    list_display_links = ("unit_address_1",)
    pass


class UnitImageAdmin(admin.ModelAdmin):
    list_display = ("__str__", "owner")
    list_display_links = ("__str__",)
    readonly_fields = ("full_size_height", "full_size_width", "thumbnail_sizes")


admin.site.register(Unit, UnitAdmin)
admin.site.register(UnitImage, UnitImageAdmin)
