import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
# from .channelsmiddleware import JWTAuthMiddlewareStack
from chats.routers import websocket_urlpatterns
from channels.sessions import CookieMiddleware
from . channel_middleware import AuthenticationMiddleware



# from Chat.routings import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': CookieMiddleware(
        AuthenticationMiddleware(

        URLRouter(
            websocket_urlpatterns
        )
        )
    )
})