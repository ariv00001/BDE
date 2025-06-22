from django import template
from django.utils.safestring import mark_safe

from fame.models import FameLevels

register = template.Library()

@register.filter()
def fametitle(fame_value):
    """
    Args:
        fame_value (int)
    Returns:
        color (str) associated with the fame level
    """
    if fame_value:
        val = int(fame_value)
        color = FameLevels.objects.get(numeric_value=val).name
    else:
        color = "gray"

    return mark_safe(color)
