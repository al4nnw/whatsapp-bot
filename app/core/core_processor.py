from fastapi.responses import JSONResponse
from redis import Redis
from app.celery_app import process_message
from app.contracts.chat_session import ChatSession
from app.contracts.message import TextMessage
from app.services.redis.chat_session.get import get_chat_session
from app.services.redis.chat_session.update import update_chat_session


import logging

logger = logging.getLogger(__name__)

from datetime import datetime, timezone
from pydantic import ValidationError
from fastapi import HTTPException

# Assume ChatSession is defined elsewhere
async def process_event(payload: dict, redis_client: Redis):
    print("Start processing event...")
    print(f"Payload: {payload}")
    try:
        statuses = get_value_from_payload(payload, "statuses")
        
        if statuses:
            print("Early return")
            return JSONResponse(content={"status": "success"}, status_code=200)
        
        message = get_value_from_payload(payload, "messages")[0]
        print(f"New message received: {message}")
        if not message:
            raise HTTPException(status_code=400, detail="Empty message received")

        user_id = message.get("from", "")

        session_key = f"chat_session:{user_id}"  # Redis key format

        # Fetch existing session or create a new one
        session_data = await redis_client.get(session_key)
        if session_data:
            print(f"Session found for user {user_id}.")
            session = ChatSession.model_validate_json(session_data)  # Deserialize JSON to ChatSession
            print("Session validated")
        else:
            print("Session not found, creating new session")
            session = ChatSession(
                user_id=user_id,
                last_message_time=datetime.now(timezone.utc),
                queue_user_messages=[],
                bot_messages=[],
                joined_user_messages=[],
                ttl_seconds=3600  # Default session TTL: 1 hour
            )
        
        # Update the session with new messages
        session.queue_user_messages.append(message)
        session.last_message_time = datetime.now(timezone.utc)
        
        # Save the updated session back to Redis
        await redis_client.set(session_key, session.model_dump_json(), ex=session.ttl_seconds)
        print("Session updated with new message")
        enqueue_time = datetime.now(timezone.utc).timestamp()
        await redis_client.set(f"{session_key}:enqueue_time", enqueue_time, ex=600)  # 10 minute expiration
        process_message.apply_async(args=(session_key, enqueue_time), countdown=10)  
        print("Message enqueued for processing")
        return JSONResponse(content={"message": "Message enqueued."}, status_code=200)

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid session data: {e}")
    except Exception as e:
        print(f"Error processing input: {e}")
        raise HTTPException(status_code=400, detail=str(e))


def get_value_from_payload(payload: dict, key: str):
    print(f"Getting value from payload: {key}")
    return payload.get("entry", [])[0].get("changes", [])[0].get("value", {}).get(key, [])

