from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/waybills/", consumers.WaybillConsumer.as_asgi()),
]