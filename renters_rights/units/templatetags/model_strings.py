from django import template

register = template.Library()


@register.simple_tag
def field_name(value, field):
    return value._meta.get_field(field).verbose_name.title()
