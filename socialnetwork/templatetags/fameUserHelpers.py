from django import template
from django.utils.safestring import mark_safe

from fame.models import FameLevels

register = template.Library()

@register.filter()
def fameTitle(fame_value):
    """
    Args:
        fame_value (int)
    Returns:
        title (str) associated with the fame level
    """
    if fame_value:
        val = int(fame_value)
        try:
            title = FameLevels.objects.get(numeric_value=val).name
            return mark_safe(title)
        except:
            raise ValueError("Invalid fame level: {}".format(fame_value))
    else:
        raise ValueError("Fame value cannot be None")


@register.filter()
def fullName(user):
    """ Assumes correct user
    """
    return mark_safe(user.first_name + " " + user.last_name)

@register.filter()
def colorOfFameValue(fame_value, type):
    if fame_value:
        if(fame_value < 0):
            return mark_safe(type+"danger")
        else:
            return mark_safe(type+"success")
    else:
        raise ValueError("Fame value cannot be None")