from email.policy import default

from django.db.models import Q, Exists, OuterRef, When, IntegerField, FloatField, Count, ExpressionWrapper, Case, Value, \
    F, Prefetch, QuerySet, Sum, Subquery, Func
from django.db.models.expressions import CombinedExpression
from rest_framework.utils.mediatypes import order_by_precedence

from fame.models import Fame, FameLevels, FameUsers, ExpertiseAreas
from socialnetwork.models import Posts, SocialNetworkUsers


# general methods independent of html and REST views
# should be used by REST and html views


def _get_social_network_user(user) -> SocialNetworkUsers:
    """Given a FameUser, gets the social network user from the request. Assumes that the user is authenticated."""
    try:
        user = SocialNetworkUsers.objects.get(id=user.id)
    except SocialNetworkUsers.DoesNotExist:
        raise PermissionError("User does not exist")
    return user


def timeline(user: SocialNetworkUsers, start: int = 0, end: int = None, published=True, community_mode=False):
    """Get the timeline of the user. Assumes that the user is authenticated."""

    if community_mode:
        # T4
        # in community mode, posts of communities are displayed if ALL of the following criteria are met:
        # 1. the author of the post is a member of the community
        # 2. the user is a member of the community
        # 3. the post contains the community’s expertise area
        # 4. the post is published or the user is the author

        pass
        #########################
        # add your code here
        #########################

    else:
        # in standard mode, posts of followed users are displayed
        _follows = user.follows.all()
        posts = Posts.objects.filter(
            (Q(author__in=_follows) & Q(published=published)) | Q(author=user)
        ).order_by("-submitted")
    if end is None:
        return posts[start:]
    else:
        return posts[start:end+1]


def search(keyword: str, start: int = 0, end: int = None, published=True):
    """Search for all posts in the system containing the keyword. Assumes that all posts are public"""
    posts = Posts.objects.filter(
        Q(content__icontains=keyword)
        | Q(author__email__icontains=keyword)
        | Q(author__first_name__icontains=keyword)
        | Q(author__last_name__icontains=keyword),
        published=published,
    ).order_by("-submitted")
    if end is None:
        return posts[start:]
    else:
        return posts[start:end+1]


def follows(user: SocialNetworkUsers, start: int = 0, end: int = None):
    """Get the users followed by this user. Assumes that the user is authenticated."""
    _follows = user.follows.all()
    if end is None:
        return _follows[start:]
    else:
        return _follows[start:end+1]


def followers(user: SocialNetworkUsers, start: int = 0, end: int = None):
    """Get the followers of this user. Assumes that the user is authenticated."""
    _followers = user.followed_by.all()
    if end is None:
        return _followers[start:]
    else:
        return _followers[start:end+1]


def follow(user: SocialNetworkUsers, user_to_follow: SocialNetworkUsers):
    """Follow a user. Assumes that the user is authenticated. If user already follows the user, signal that."""
    if user_to_follow in user.follows.all():
        return {"followed": False}
    user.follows.add(user_to_follow)
    user.save()
    return {"followed": True}


def unfollow(user: SocialNetworkUsers, user_to_unfollow: SocialNetworkUsers):
    """Unfollow a user. Assumes that the user is authenticated. If user does not follow the user anyway, signal that."""
    if user_to_unfollow not in user.follows.all():
        return {"unfollowed": False}
    user.follows.remove(user_to_unfollow)
    user.save()
    return {"unfollowed": True}


def submit_post(
    user: SocialNetworkUsers,
    content: str,
    cites: Posts = None,
    replies_to: Posts = None,
):
    """Submit a post for publication. Assumes that the user is authenticated.
    returns a tuple of three elements:
    1. a dictionary with the keys "published" and "id" (the id of the post)
    2. a list of dictionaries containing the expertise areas and their truth ratings
    3. a boolean indicating whether the user was banned and logged out and should be redirected to the login page
    """

    # create post instance:
    post = Posts.objects.create(
        content=content,
        author=user,
        cites=cites,
        replies_to=replies_to,
    )

    # classify the content into expertise areas:
    # only publish the post if none of the expertise areas contains bullshit:
    _at_least_one_expertise_area_contains_bullshit, _expertise_areas = (
        post.determine_expertise_areas_and_truth_ratings()
    )
    post.published = not _at_least_one_expertise_area_contains_bullshit

    redirect_to_logout = False


    ######################### TODO: This is my solution to T1
    negative_user_expertise_areas = (
        user.expertise_area
            .filter(fame__fame_level__gt=0)
            .values_list("expertiseareas__pk", flat=True)
    )
    expertise_areas_in_post = [e["expertise_area"].id for e in _expertise_areas]
    #print(expertise_areas_in_post, negative_user_expertise_areas)
    #print(set(negative_user_expertise_areas) & set(expertise_areas_in_post))
    all_expertise_areas_that_are_negative_fame_for_user_and_in_post = set(negative_user_expertise_areas) & set(expertise_areas_in_post)
    post.published = post.published and (len(all_expertise_areas_that_are_negative_fame_for_user_and_in_post) == 0) #negative_user_expertise_areas.intersection(QuerySet(_expertise_areas)).count() == 0
    ######################### TODO: This is the end of my solution for T1

    ######################### TODO: This is my solution for T2
    def lowerFame():
        #print(_expertise_areas)
        expertise_areas_with_negative_thruth_rating = [e["expertise_area"].id for e in _expertise_areas if e["truth_rating"] is not None and e["truth_rating"].numeric_value < 0]
        #print(expertise_areas_with_negative_thruth_rating)
        for expertise_area in expertise_areas_with_negative_thruth_rating:
            previous_fame, created = Fame.objects.get_or_create(
                user = user,
                expertise_area=expertise_area,
                defaults = {"fame_level": FameLevels.objects.get(numeric_value = -10)} # -10 is 'Confuser' (see fakedata line 123)
            )
            if(created): # e.g. we had to create the Expertise_area
                continue # we skip the rest

            #e.g. if we need to lower the existing fame
            try:
                updatedFame = {"fame_level": previous_fame.fame_level.get_next_lower_fame_level()}
                Fame.objects.filter( # use filter instead of get
                    user=user,
                    expertise_area=expertise_area
                ).update(**updatedFame)
                '''
                Fame.objects.update_or_create( # Info: we could also use user._do_update(...) or Fame.objects.update(...), since we know that the entry exists. (So no create ever done)
                    user=user,
                    expertise_area = expertise_area,
                    defaults = updatedFame, create_defaults = updatedFame
                )
                '''
            except ValueError: # this happens, if we cannot decrease the fame anymore
                #e.g. delete/ bann user
                deleteUser()
                return True # logout
        return False # no logout

    def deleteUser():
        # Deactivate user
        FameUsers.objects.update_or_create( #TODO: could filter
            id = user.id,
            defaults = {"is_active": False},
        )

        # Unpublish all posts
        Posts.objects.filter(
            author=user.id
        ).update(published=False)



    if (_at_least_one_expertise_area_contains_bullshit):
        redirect_to_logout = lowerFame()
    ######################### TODO: This is the end of my solution for T2

    post.save()

    return (
        {"published": post.published, "id": post.id},
        _expertise_areas,
        redirect_to_logout,
    )


def rate_post(
    user: SocialNetworkUsers, post: Posts, rating_type: str, rating_score: int
):
    """Rate a post. Assumes that the user is authenticated. If user already rated the post with the given rating_type,
    update that rating score."""
    user_rating = None
    try:
        user_rating = user.userratings_set.get(post=post, rating_type=rating_type)
    except user.userratings_set.model.DoesNotExist:
        pass

    if user == post.author:
        raise PermissionError(
            "User is the author of the post. You cannot rate your own post."
        )

    if user_rating is not None:
        # update the existing rating:
        user_rating.rating_score = rating_score
        user_rating.save()
        return {"rated": True, "type": "update"}
    else:
        # create a new rating:
        user.userratings_set.add(
            post,
            through_defaults={"rating_type": rating_type, "rating_score": rating_score},
        )
        user.save()
        return {"rated": True, "type": "new"}


def fame(user: SocialNetworkUsers):
    """Get the fame of a user. Assumes that the user is authenticated."""
    try:
        user = SocialNetworkUsers.objects.get(id=user.id)
    except SocialNetworkUsers.DoesNotExist:
        raise ValueError("User does not exist")

    return user, Fame.objects.filter(user=user)


def bullshitters():
    """Return a Python dictionary mapping each existing expertise area in the fame profiles to a list of the users
    having negative fame for that expertise area. Each list should contain Python dictionaries as entries with keys
    ``user'' (for the user) and ``fame_level_numeric'' (for the corresponding fame value), and should be ranked, i.e.,
    users with the lowest fame are shown first, in case there is a tie, within that tie sort by date_joined
    (most recent first). Note that expertise areas with no expert may be omitted.
    """
    ######################### TODO: This is my solution for T3
    all_bullshitters = (
        FameLevels.objects
        .select_related("fame__user","fame__expertise_area")
        .filter(numeric_value__lt=0)
        .values("numeric_value","fame__user","fame__expertise_area")
        .annotate(fame_level_numeric=F("numeric_value"),
                  user=F("fame__user"),
                  expertise_area=F("fame__expertise_area"))
        .values("fame_level_numeric","user","fame__expertise_area__label")#,"name")
        .filter(user__isnull=False, expertise_area__isnull=False)
        .order_by("fame_level_numeric","-fame__user__date_joined") # aufsteigendes fame level bedeutet, dass zuerst die 'negativsten' Werte kommen
        #.group_by("expertise_area") # geht leider nicht           # absteigende daten bedeuten, dass die größten werte (2025) vor den älteren (1999) kommen
     )

    #print(all_bullshitters)
    bullshitters_by_expertise_area = {}
    for entry in all_bullshitters: # they are ordered, thus I will traverse them
        bullshitters_by_expertise_area.setdefault(entry["fame__expertise_area__label"],[]).append({
                "user": entry["user"],
                "fame_level_numeric": entry["fame_level_numeric"],
            })
    #print(bullshitters_by_expertise_area)
    return bullshitters_by_expertise_area
    ######################### TODO: This is the end of my solution for T3




def join_community(user: SocialNetworkUsers, community: ExpertiseAreas):
    """Join a specified community. Note that this method does not check whether the user is eligible for joining the
    community.
    """
    pass
    #########################
    # add your code here
    #########################



def similar_users(user: SocialNetworkUsers):
    """Compute the similarity of user with all other users. The method returns a QuerySet of FameUsers annotated
    with an additional field 'similarity'. Sort the result in descending order according to 'similarity', in case
    there is a tie, within that tie sort by date_joined (most recent first)"""

    ######################### TODO: This is my solution for T5
    class Abs(Func):
        function = 'ABS'

    # create all cases for user's expertise_area's
    user_expretise_area_case_when_clauses = []
    # match existing area
    for area in user.expertise_area.all():
        user_fame_numeric_value = Fame.objects.filter(user=user.id, expertise_area=area).values_list("fame_level__numeric_value").first()[0]
        user_expretise_area_case_when_clauses.append(
            When(
                expertise_area=area,
                then=ExpressionWrapper(Abs(F("fame_level__numeric_value") - user_fame_numeric_value), output_field=IntegerField())
            )
        )

    similar_users = (
        Fame.objects
            .exclude(user=user)
            .select_related("fame_users")
            .annotate(difference = Case(
                *user_expretise_area_case_when_clauses,
                default=Value(999),
                output_field=IntegerField()
                )
            )
            .values("user")
            .annotate(similarity= Count(Q(difference__lt=100), filter=Q(difference__lte=100)) / Value(user.expertise_area.count().__float__()))
        )

    annotated_fame_users = (
        FameUsers.objects
            .exclude(id=user.id)
            .annotate(similarity = Subquery(
                similar_users
                    .filter(user=OuterRef("id"))
                    .values("similarity")
                )
            )
            .order_by("-similarity", "date_joined")
            .filter(similarity=0)
    )

    return annotated_fame_users
    ######################### TODO: This is the end of my solution for T5



def leave_community(user: SocialNetworkUsers, community: ExpertiseAreas):
    """Leave a specified community."""
    pass
    #########################
    # add your code here
    #########################

