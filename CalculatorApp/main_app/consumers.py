import json
import asyncio
from channels.layers import get_channel_layer
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

from main_app.utils import get_result_history

class SyncConsumer(AsyncWebsocketConsumer):
    _connections = 0
    _sync_task = None

    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("sync_group", self.channel_name)
        SyncConsumer._connections += 1
        if SyncConsumer._connections == 1:
            SyncConsumer._sync_task = asyncio.create_task(
                self._periodic_sync()
            )
        # initial sync
        history = await get_result_history()
        await self.send(text_data=json.dumps(history))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("sync_group", self.channel_name)
        SyncConsumer._connections -= 1
        
        if SyncConsumer._connections == 0 and SyncConsumer._sync_task:
            SyncConsumer._sync_task.cancel()
            try:
                await SyncConsumer._sync_task
            except asyncio.CancelledError:
                pass
            SyncConsumer._sync_task = None

    @staticmethod
    async def _periodic_sync():
        """Background task that sends messages periodically"""
        channel_layer = get_channel_layer()
        while True:
            await asyncio.sleep(settings.SYNC_PERIOD)
            history = await get_result_history()
            await channel_layer.group_send(
                "sync_group",
                {
                    "type": "sync.message",
                    "message": json.dumps(history)
                }
            )

    async def sync_message(self, event):
        """Handler for group_send messages"""
        await self.send(text_data=event["message"])