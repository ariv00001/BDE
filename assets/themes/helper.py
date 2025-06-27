import os

from django.shortcuts import render


def ownRender(request, template_name, context={}, content_type=None, status=None, using=None):
    if request.session.get("theme"): context.update( {"theme": request.session.get("theme")} )
    context.update({"user": request.user,})
    #print("Request send with context:", context)
    return render(request, template_name, context=context, content_type=content_type, status=status, using=using)

def themeNameToPath(themeName):
    if themeName == "auto":
        return 'bootstrap.min.css'
    return 'themes/'+themeName+'.min.css'
