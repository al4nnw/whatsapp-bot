from redis import Redis
from app.contracts.chat_session import ChatSession

# Update the chat session in Redis
async def update_chat_session(session: ChatSession, redis: Redis):
  await redis.set(session.id, session.model_dump_json())

# Update TTL of the chat session in Redis
async def update_chat_session_ttl(session_id: str, ttl_seconds: int, redis: Redis):
  await redis.expire(session_id, ttl_seconds)
