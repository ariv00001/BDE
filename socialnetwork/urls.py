from django.urls import path

from socialnetwork.views.html import timeline, bullshitters, toggle_community_mode, join_community, leave_community
from socialnetwork.views.html import follow
from socialnetwork.views.html import unfollow
from socialnetwork.views.rest import PostsListApiView

app_name = "socialnetwork"

urlpatterns = [
    path("api/posts", PostsListApiView.as_view(), name="posts_fulllist"),
    path("html/timeline", timeline, name="timeline"),
    path("api/follow", follow, name="follow"),
    path("api/unfollow", unfollow, name="unfollow"),

    path("html/bullshitters", bullshitters, name="bullshitters"),

    path("toggle_community/", toggle_community_mode, name="toggle_community_mode"),
    path("join_community/", join_community, name="join_community"),
    path("leave_community", leave_community, name="leave_community"),
]
