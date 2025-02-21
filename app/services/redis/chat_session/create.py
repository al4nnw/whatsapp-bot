# Store the chat session in Redis

from redis import Redis
from app.contracts.chat_session import ChatSession

async def create_chat_session(session: ChatSession, redis: Redis):
  await redis.set(session.id, session.model_dump_json())
