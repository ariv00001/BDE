from django import template
from django.utils.safestring import mark_safe

from assets.themes.helper import themeNameToPath
from fame.models import FameLevels

register = template.Library()

@register.filter()
def parseTheme(theme):
    return mark_safe(themeNameToPath(theme))