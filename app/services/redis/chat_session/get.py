# Get the chat session from Redis

from redis import Redis
from app.contracts.chat_session import ChatSession

async def get_chat_session(session_id: str, redis: Redis) -> ChatSession:
  session_data = await redis.get(session_id)
  if not session_data:
    raise ValueError("Session not found")
  return ChatSession.model_validate_json(session_data)