import aiohttp
from celery import Celery
import os
import asyncio
from app.contracts.chat_session import ChatSession
from app.services.redis.redis_client import get_redis_client
from app.worker.generate_response import generate_response

celery_app = Celery(
    __name__,
    broker=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:6379/0",
    backend=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:6379/0",    
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Environment variables validation omitted for brevity (keep existing checks)

# Retrieve environment variables
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION")
ACCESS_TOKEN = os.getenv("WHATSAPP_TOKEN")

# Validate required environment variables so that issues are caught early.
if not PHONE_NUMBER_ID:
    raise ValueError("Environment variable PHONE_NUMBER_ID is not set.")
if not WHATSAPP_API_VERSION:
    raise ValueError("Environment variable WHATSAPP_API_VERSION is not set.")
if not ACCESS_TOKEN:
    raise ValueError("Environment variable WHATSAPP_TOKEN is not set.")

WHATSAPP_API_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{PHONE_NUMBER_ID}/messages"




@celery_app.task(bind=True)
def process_message(self, topic, enqueue_time):
    return asyncio.run(process_message_async(topic, enqueue_time))

async def process_message_async(topic, enqueue_time):
    print(f"Celery Worker - Processing message for topic {topic} (enqueued at {enqueue_time})...")

    redis_client = await get_redis_client()
    
    # Check for newer requests
    current_enqueue_time = await redis_client.get(f"{topic}:enqueue_time")
    if current_enqueue_time:
        current_enqueue_time = float(current_enqueue_time)
        if current_enqueue_time > enqueue_time:
            print(f"Skipping processing: Newer request exists ({current_enqueue_time} > {enqueue_time})")
            return

    # Existing session processing logic
    session_key = topic
    session = await redis_client.get(session_key)
    if not session:
        print(f"Session not found for topic {topic}")
        return

    if isinstance(session, bytes):
        session = session.decode("utf-8")
    try:
        session = ChatSession.model_validate_json(session)
    except Exception as e:
        print(f"Failed to validate session data: {e}")
        return
    
    if not session.has_user_messages:
        print("No user messages, skipping")
        return
    
    
    message = await generate_response(session)    
    
    session.bot_messages.append(message)
    
    try:
        result = await send_whatsapp_message(session.user_id, message)
        print(f"WhatsApp response: {result}")
    except Exception as e:
        print(f"Failed to send message: {e}")
        return
        
    await redis_client.set(session_key, session.model_dump_json())
    print(f"Finished processing {topic}")

    


async def send_whatsapp_message(user_id: str, bot_reply: str):    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": user_id,
        "type": "text",
        "text": {
            "body": bot_reply
        }
    }
    
    print(f"[send_whatsapp_message] body: {data}")
    
    async with aiohttp.ClientSession() as aio_req:
        async with aio_req.post(WHATSAPP_API_URL, headers=headers, json=data) as response:
            response.raise_for_status()
            result = await response.json()
    
    print(f"Sending WhatsApp message: {bot_reply}")
    return {"message": "Bot response sent.", "response": result}
