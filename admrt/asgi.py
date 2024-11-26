import os

# from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import newChat.routing
from newChat.middleware import JWTAuthMiddleware  # Import the JWT middleware


django_asgi_app = get_asgi_application()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "admrt.settings")
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": 
        AuthMiddlewareStack(  # Retain the AuthMiddlewareStack
            URLRouter(
                newChat.routing.websocket_urlpatterns
            )
        )
    
})

ASGI_APPLICATION = 'admrt.asgi.application'
