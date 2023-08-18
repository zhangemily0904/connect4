"""webapps URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from connect4 import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home_action, name='home'),
    path('oauth/', include('social_django.urls', namespace='social')),
    path('logout', auth_views.logout_then_login, name='logout'),
    path('global', views.global_action, name="global"),
    path('create-room', views.create_room_action, name="create-room"),
    path('join-room/<int:room_id>', views.join_room_action, name="join-room"),
    path('leaderboard', views.leaderboard_action, name="leaderboard"),
    path('friends', views.friends_action, name="friends"),
    path('profile', views.profile_action, name="profile"),
    path('friend_profile/<int:user_id>', views.friend_profile_action, name='friend-profile'),
    path('unfriend/<int:user_id>', views.unfriend, name='unfriend'),
    path('friend/<int:user_id>', views.friend, name='friend'),
    path('challenge/<int:user_id>', views.challenge, name='challenge'),
    path('get-gameplay', views.get_gameplay, name="get-gameplay"),
    path('drop-token', views.drop_token, name="drop-token"),
    path('get-global', views.get_global, name="get-global"),
    path('get_token_photo/<int:user_id>', views.get_token_photo, name="get-token-photo"),
    path('end-game', views.end_game, name="end-game"),
    path('time-out', views.time_out, name="time-out"),
    path('decline_challenge/<int:room_id>', views.decline_challenge, name="decline-challenge"),
    path('cancel_challenge/<int:room_id>', views.cancel_challenge, name="cancel-challenge"),
]
