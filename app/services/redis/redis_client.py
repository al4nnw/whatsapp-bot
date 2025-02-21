import redis.asyncio as aioredis

async def get_redis_client():
    return aioredis.from_url("redis://redis:6379", encoding="utf-8", decode_responses=True)
