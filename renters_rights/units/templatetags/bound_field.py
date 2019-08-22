from django import template

register = template.Library()


@register.simple_tag
def bound_field(form, name):
    return form.__getitem__(name)
