import aio_pika
import ujson as json

from ....settings.conf import settings


async def publish_message(channel: aio_pika.abc.AbstractChannel, message: dict):
        exchange = await channel.declare_exchange("events", aio_pika.ExchangeType.TOPIC)
        await exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key=''
        )
