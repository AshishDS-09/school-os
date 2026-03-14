# backend/app/events/subscriber.py

import asyncio
import redis.asyncio as aioredis
import os

async def listen():
    print("Event subscriber starting...")
    client = aioredis.from_url(
        os.getenv("REDIS_URL", "redis://redis:6379/0")
    )
    pubsub = client.pubsub()
    await pubsub.subscribe("marks.entered", "attendance.marked")
    print("Subscribed to events. Waiting...")
    async for message in pubsub.listen():
        if message["type"] == "message":
            print(f"Event received: {message['data']}")
            # Agents will be routed here in Phase 4

if __name__ == "__main__":
    asyncio.run(listen())