from django import template

register = template.Library()


@register.simple_tag
def field_name(value, field):
    """
    Django template filter which returns the verbose name of an object's,
    model's or related manager's field.
    """
    if hasattr(value, "model"):
        value = value.model

    return value._meta.get_field(field).verbose_name.title()
