import os
import django
from django.core.asgi import get_asgi_application

# Initialize Django settings and apps before importing routing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'magnetapp_backend.settings')
django.setup()
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
