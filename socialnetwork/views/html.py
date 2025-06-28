from zoneinfo import available_timezones

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from assets.themes.helper import ownRender
from fame.models import ExpertiseAreas
from socialnetwork import api
from socialnetwork.api import _get_social_network_user
from socialnetwork.models import SocialNetworkUsers
from socialnetwork.serializers import PostsSerializer


@require_http_methods(["GET"])
@login_required
def timeline(request):
    # using the serializer to get the data, then use JSON in the template!
    # avoids having to do the same thing twice

    # initialize community mode to False the first time in the session
    if 'community_mode' not in request.session:
        request.session['community_mode'] = False

    ########### T7 ################
    # getting the authenticated user
    user = _get_social_network_user(request.user)

    # getting the community data
    joined_communities = user.communities.all()

    # communities that is available to the user for joining based on their Super Pro threshold
    available_communities = api.get_available_communities(user)

    # get extra URL parameters:
    keyword = request.GET.get("search", "")
    published = request.GET.get("published", True)
    error = request.GET.get("error", None)

    # if keyword is not empty, use search method of API:
    if keyword and keyword != "":
        posts = api.search(keyword, published=published)
    else:
        posts = api.timeline(
            user,
            published=published,
            community_mode=request.session['community_mode']
        )

    # now building the context
    context = {
        "posts": PostsSerializer(posts, many=True).data,
        "searchkeyword": keyword,
        "error": error,
        "followers": list(api.follows(user).values_list("id", flat=True)),

        # adding community data
        "joined_communities": joined_communities,
        "available_communities": available_communities,
        "community_mode": request.session['community_mode'],
    }

    # if keyword and keyword != "":
    #     context = {
    #         "posts": PostsSerializer(
    #             api.search(keyword, published=published), many=True
    #         ).data,
    #         "searchkeyword": keyword,
    #         "error": error,
    #         "followers": list(api.follows(_get_social_network_user(request.user)).values_list('id', flat=True)),
    #     }
    # else:  # otherwise, use timeline method of API:
    #
    #     context = {
    #         "posts": PostsSerializer(
    #             api.timeline(
    #                 _get_social_network_user(request.user),
    #                 published=published,
    #             ),
    #             many=True,
    #         ).data,
    #         "searchkeyword": "",
    #         "error": error,
    #         "followers": list(api.follows(_get_social_network_user(request.user)).values_list('id', flat=True)),
    #     }

    return ownRender(request, "timeline.html", context=context)


@require_http_methods(["POST"])
@login_required
def follow(request):
    user = _get_social_network_user(request.user)
    user_to_follow = SocialNetworkUsers.objects.get(id=request.POST.get("user_id"))
    api.follow(user, user_to_follow)
    return redirect(reverse("sn:timeline"))


@require_http_methods(["POST"])
@login_required
def unfollow(request):
    user = _get_social_network_user(request.user)
    user_to_unfollow = SocialNetworkUsers.objects.get(id=request.POST.get("user_id"))
    api.unfollow(user, user_to_unfollow)
    return redirect(reverse("sn:timeline"))


@require_http_methods(["GET"])
@login_required
def bullshitters(request):
    context = {
        "bulshitters": api.bullshitters(), # now, I can use {% for b in bulshitters %} in bulshitters.html
    }
    return ownRender(request, "bulshitters.html", context=context)


@require_http_methods(["POST"])
@login_required
def toggle_community_mode(request):
    request.session["community_mode"] = not request.session.get("community_mode", False)
    return redirect(reverse("sn:timeline"))

@require_http_methods(["POST"])
@login_required
def join_community(request):
    # T7
    user = _get_social_network_user(request.user)
    community_id = request.POST.get("community_id")  # Use "community_id" for sending the POST request
    if not community_id:
        raise ValueError("No community_id provided")

    community_to_join = ExpertiseAreas.objects.get(id=community_id)

    if not user.communities.filter(id=community_id).exists():
        api.join_community(user, community_to_join)

    return redirect(reverse("sn:timeline"))

@require_http_methods(["POST"])
@login_required
def leave_community(request):
    # T7
    user = _get_social_network_user(request.user)
    community_id = request.POST.get("community_id") # Use "community_id" for sending the POST request
    if not community_id:
        raise ValueError("No community_id provided")

    community_to_leave = ExpertiseAreas.objects.get(id=community_id)

    if user.communities.filter(id=community_id).exists():
        api.leave_community(user, community_to_leave)

    return redirect(reverse("sn:timeline"))

@require_http_methods(["GET"])
@login_required
def similar_users(request):
    raise NotImplementedError("Not implemented yet")



######################
#ADDITIONAL: Addinitonal functionality

@require_http_methods(["GET"])
@login_required
def communities(request):
    user = _get_social_network_user(request.user)
    community_id = request.GET.get("community_id")
    #try:
    community_id = int(community_id)
    community = user.communities.get(id=community_id)
    if api.userInCommunity(user, community):
        context = {
            "expertiseArea": community,
            "users": api.communitySocialNetworkUsers(community),
        }
        return ownRender(request, "communities.html", context=context)
    #except:
    #    pass
    return redirect(reverse("sn:errorpage"))


@require_http_methods(["GET", "POST"])
def errorpage(request):
    return render(request, "errorpage.html")

@require_http_methods(["GET"])
@login_required
def change_theme(request):
    theme_name = request.GET.get('theme')
    if theme_name:
        request.session['theme'] = theme_name
        return redirect('home')
    else:
        return redirect(reverse("sn:errorpage"))

@require_http_methods(["GET"])
@login_required
def similarusers(request):
    user = _get_social_network_user(request.user)
    context = {
        "similarUsers": api.similar_users(user),
    }
    return ownRender(request, "similarUsers.html", context=context)