# Delete the chat session from Redis

from redis import Redis

async def delete_chat_session(session_id: str, redis: Redis):
  await redis.delete(session_id)

