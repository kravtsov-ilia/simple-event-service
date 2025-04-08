import asyncio
from contextlib import asynccontextmanager

import aio_pika
import ujson as json
from beanie import init_beanie
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from motor.motor_asyncio import AsyncIOMotorClient

from ...domain.models import Notification, EventInfo, Topics
from ...settings.conf import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo_client = AsyncIOMotorClient(settings.MONGO_URI)
    await init_beanie(database=mongo_client.notification_db, document_models=[Notification])
    asyncio.create_task(consume())
    yield

app = FastAPI(lifespan=lifespan)


events_subscribers = {
    Topics.created: set(),
    Topics.updated: set(),
    Topics.deleted: set(),
}

owners_sockets_map: dict[str, WebSocket] = {}


@app.websocket("/ws/notifications/{topic}")
async def websocket_endpoint(websocket: WebSocket, topic: Topics):
    await websocket.accept()
    events_subscribers[topic].add(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        events_subscribers[topic].remove(websocket)


async def notify_clients(notification: Notification, topic: Topics):
    topics_list = [Topics.created, Topics.updated, Topics.deleted] if topic == Topics.created else [topic]

    for topic in topics_list:
        for client in list(events_subscribers[topic]):
            try:
                await client.send_json(notification.model_dump(exclude={"id", "created_at"}))
            except IOError:
                events_subscribers[topic].remove(client)


async def consume():
    connection = await aio_pika.connect_robust(settings.RABBIT_URI)
    channel = await connection.channel()
    exchange = await channel.declare_exchange("events", aio_pika.ExchangeType.TOPIC)
    queue = await channel.declare_queue("notifications", durable=True)
    await queue.bind(exchange, routing_key='')

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                event_data = json.loads(message.body)
                topic = event_data['action']

                notification_doc = Notification(
                    type="notification",
                    notification_type=f"event.{event_data['action']}",
                    event=EventInfo(
                        id=event_data["id"],
                        title=event_data["title"],
                        action=event_data["action"],
                        user=event_data["user"],
                        timestamp=event_data["timestamp"]
                    ),
                    user=event_data["user"]
                )
                await notification_doc.create()
                await notify_clients(notification_doc, Topics(topic))
