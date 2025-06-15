from django.urls import re_path

from . consumers import *

websocket_urlpatterns = [
 re_path(r'ws/chat/(?P<room_name>[\w-]+)/$', ChatConsumer.as_asgi()),
 re_path(r'ws/video-call/(?P<room_name>[\w-]+)/$', VideoCallConsumer.as_asgi()),
]