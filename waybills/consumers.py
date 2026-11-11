import json
from channels.generic.websocket import AsyncWebsocketConsumer

class WaybillConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Создаем "комнату", к которой будут подключаться все браузеры
        self.room_group_name = "waybills_updates"

        # Добавляем текущий браузер в эту комнату
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Удаляем браузер из комнаты при закрытии страницы
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Этот метод вызывается, когда Django отправляет сообщение в комнату
    async def waybill_update(self, event):
        # Отправляем сообщение в браузер (в JavaScript)
        await self.send(text_data=json.dumps({
            "type": "waybill_updated",
            "waybill_id": event["waybill_id"]
        }))

        # Этот метод вызывается при изменении порядка
    async def waybills_reordered(self, event):
        await self.send(text_data=json.dumps({
            "type": "waybills_reordered"
        }))