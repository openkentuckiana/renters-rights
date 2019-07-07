from django.contrib import admin

from lib.admin import SoftDeleteModelAdmin

from .models import Unit, UnitImage


class UnitImageAdmin(admin.ModelAdmin):
    readonly_fields = ("full_size_height", "full_size_width", "thumbnail_sizes")


admin.site.register(Unit, SoftDeleteModelAdmin)
admin.site.register(UnitImage, UnitImageAdmin)
