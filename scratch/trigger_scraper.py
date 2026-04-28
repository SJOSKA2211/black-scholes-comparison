
import asyncio
import json
from datetime import date
import aio_pika

async def trigger():
    connection = await aio_pika.connect_robust("amqp://admin:JKmaish2025@localhost:5672/")
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange("bs.tasks", type=aio_pika.ExchangeType.DIRECT, durable=True)
        
        payload = json.dumps({"market": "spy", "date": date.today().isoformat()}).encode()
        # Note: In production it's compressed, but the consumer handles it if content_encoding is set.
        # Actually, let's compress it to match the standard.
        import gzip
        body = gzip.compress(payload)
        
        await exchange.publish(
            aio_pika.Message(
                body=body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_encoding="gzip",
                content_type="application/json",
            ),
            routing_key="scrape",
        )
        print("Scrape task published for SPY")

if __name__ == "__main__":
    asyncio.run(trigger())
