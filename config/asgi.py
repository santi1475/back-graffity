import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
import pos.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Obtenemos la app HTTP primero
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        URLRouter(
            pos.routing.websocket_urlpatterns
        )
    ),
})