from django import template

register = template.Library()


@register.filter
def times(number):
    return range(1, number + 1)


@register.filter
def short_address(value):
    if "," in value:
        return value.split(",", 1)[1].strip()
    return value
