from django import template
from django.utils.functional import SimpleLazyObject
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
    #if fame_value:
    val = int(fame_value)
    try:
        title = FameLevels.objects.get(numeric_value=val).name
        return mark_safe(title)
    except:
        raise ValueError("Invalid fame level: {}".format(fame_value))
    #else:
    #    raise ValueError("Fame value cannot be {}".format(fame_value))


@register.filter()
def fullName(user):
    """ Assumes correct user
    """
    return mark_safe(user.first_name + " " + user.last_name)

@register.filter()
def colorOfFameValue(fame_value, type):
    #if fame_value:
    if(fame_value < 0):
        return mark_safe(type+"danger")
    else:
        return mark_safe(type+"success")
    #else:
    #    raise ValueError("Fame value cannot be None")

@register.filter()
def asVar(string):
    return mark_safe("_".join( string.split() ))

@register.filter()
def userCredentials(user, currentUser=None):
    print(user, currentUser)
    if(user != currentUser): return mark_safe('''
    <b><a href="/fame/html/fame?userid={}">{}</a></b>
    
    <span style="color:gray">{}</span>
    '''.format( user.id, fullName(user), user.email))

    else: return mark_safe('''
    <b><a href="/fame/html/fame?userid={}">{}</a></b>
    (You)
    <span style="color:gray">{}</span>
    '''.format( user.id, fullName(user), user.email))

@register.filter()
def userHighlight(user, currentUser=None):
    return "bg-info-subtle" if user==currentUser else ""

@register.filter()
def isUser(user, currentUser=None):
    print(user, currentUser, "JI")
    return user == currentUser

@register.filter()
def simInPercent(similarity):
    return f"{(similarity * 100):0.4g}"
