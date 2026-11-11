import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import waybills.routing  # <--- Ссылаемся на наш будущий файл маршрутов

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

application = ProtocolTypeRouter({
    # Обычные HTTP-запросы идут сюда
    "http": get_asgi_application(),
    # WebSockets идут сюда (с проверкой авторизации)
    "websocket": AuthMiddlewareStack(
        URLRouter(
            waybills.routing.websocket_urlpatterns
        )
    ),
})