import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ScanConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extraemos el UUID de la URL
        self.channel_uuid = self.scope['url_route']['kwargs']['channel_uuid']
        self.group_name = f"scan_{self.channel_uuid}"

        # Unimos este cliente al grupo (canal) de Redis
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Lo sacamos del grupo al desconectarse
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Este método escucha el evento "product.scanned" que despachamos en services.py
    async def product_scanned(self, event):
        # Enviamos la data al cliente frontend conectado
        await self.send(text_data=json.dumps({
            'event': 'product.scanned',
            'barcode': event['barcode'],
            'productData': event['productData']
        }))