"""forumServer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
import forumServer.dbHandler

urlpatterns = [
   # General methods
    url(r'^db/api/clear/', forumServer.dbHandler.clear),
    url(r'^db/api/status/', forumServer.dbHandler.status),
   # User (completed)
    url(r'^db/api/user/create/', forumServer.dbHandler.userCreate),
    url(r'^db/api/user/details/', forumServer.dbHandler.getUserDetails),
    url(r'^db/api/user/follow/', forumServer.dbHandler.userFollow),
    url(r'^db/api/user/unfollow/', forumServer.dbHandler.userUnfollow),
    url(r'^db/api/user/listFollowers/', forumServer.dbHandler.getFollowers),
    url(r'^db/api/user/listFollowing/', forumServer.dbHandler.getFollowee),
    url(r'^db/api/user/updateProfile/', forumServer.dbHandler.userUpdate),
    url(r'^db/api/user/listPosts/', forumServer.dbHandler.getUserPosts),
   # Forum
    url(r'^db/api/forum/create/', forumServer.dbHandler.forumCreate),
    url(r'^db/api/forum/details/', forumServer.dbHandler.getForumDetails),
    url(r'^db/api/forum/listPosts/', forumServer.dbHandler.getForumsPostList),
    url(r'^db/api/forum/listUsers/', forumServer.dbHandler.forumUserList),
    url(r'^db/api/forum/listThreads/', forumServer.dbHandler.forumThreadList),
   # Post
    url(r'^db/api/post/create/', forumServer.dbHandler.postCreate),
    url(r'^db/api/post/details/', forumServer.dbHandler.getPostDetails),
    url(r'^db/api/post/list/', forumServer.dbHandler.getPostList),
    url(r'^db/api/post/remove/', forumServer.dbHandler.postRemove),
    url(r'^db/api/post/restore/', forumServer.dbHandler.postRestore),
    url(r'^db/api/post/update/', forumServer.dbHandler.postUpdate),
    url(r'^db/api/post/vote/', forumServer.dbHandler.postVote),
   # Thread
    url(r'^db/api/thread/close/', forumServer.dbHandler.threadClose),
    url(r'^db/api/thread/create/', forumServer.dbHandler.threadCreate),
    url(r'^db/api/thread/details/', forumServer.dbHandler.getThreadDetails),
    url(r'^db/api/thread/list/', forumServer.dbHandler.threadList),
    url(r'^db/api/thread/listPosts/', forumServer.dbHandler.getThreadPosts),
    url(r'^db/api/thread/open/', forumServer.dbHandler.threadOpen),
    url(r'^db/api/thread/close/', forumServer.dbHandler.threadClose),
    url(r'^db/api/thread/remove/', forumServer.dbHandler.threadRemove),
    url(r'^db/api/thread/restore/', forumServer.dbHandler.threadRestore),
    url(r'^db/api/thread/subscribe/', forumServer.dbHandler.threadSubscribe),
    url(r'^db/api/thread/unsubscribe/', forumServer.dbHandler.threadUnsubscribe),
    url(r'^db/api/thread/update/', forumServer.dbHandler.threadUpdate),
    url(r'^db/api/thread/vote/', forumServer.dbHandler.threadVote),
]
