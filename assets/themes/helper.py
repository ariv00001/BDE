import os

from django.shortcuts import render

from socialnetwork.api import _get_social_network_user


def ownRender(request, template_name, context={}, content_type=None, status=None, using=None, current_page_adress="#"):
    if request.session.get("theme"): context.update( {"theme": request.session.get("theme")} )
    context.update({"user": _get_social_network_user(request.user),})
    if(context["user"] and context["user"] and request.session.get("community_mode", False)):
        context.update({"joined_communities": context["user"].communities.all()})
    context.update({"current_page_address": current_page_adress})
    #print("Request send with context:", context)
    return render(request, template_name, context=context, content_type=content_type, status=status, using=using)

def themeNameToPath(themeName):
    if themeName == "auto":
        return 'bootstrap.min.css'
    return 'themes/'+themeName+'.min.css'
