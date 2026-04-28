
import asyncio
import json
from datetime import date
import aio_pika
import gzip

async def trigger():
    connection = await aio_pika.connect_robust("amqp://admin:JKmaish2025@localhost:5672/")
    async with connection:
        channel = await connection.channel()
        
        # Publish directly to the queue by using the default exchange (empty string)
        # and the queue name as the routing key.
        payload = json.dumps({"market": "spy", "date": date.today().isoformat()}).encode()
        body = gzip.compress(payload)
        
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_encoding="gzip",
                content_type="application/json",
            ),
            routing_key="bs.scrape",
        )
        print("Scrape task published directly to bs.scrape queue")

if __name__ == "__main__":
    asyncio.run(trigger())
