import os
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.concurrency import asynccontextmanager
from fastapi.responses import JSONResponse
from app.core.core_processor import process_event
from app.services.redis.redis_client import get_redis_client

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

if not VERIFY_TOKEN:
    raise ValueError("Environment variable VERIFY_TOKEN is not set.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Redis connection
    app.state.redis = await get_redis_client()
    try:
        yield
    finally:
        # Shutdown: Close Redis connection
        await app.state.redis.close()

async def get_redis():
    return app.state.redis


app = FastAPI(lifespan=lifespan)


@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),  # WhatsApp uses string challenges
    hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    """
    Verification endpoint.
    
    WhatsApp (via Facebook) sends a GET request with these query parameters.
    If the verify token matches, we return the challenge.
    """
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return JSONResponse(content=int(hub_challenge))  # Convert challenge to integer
    else:
        raise HTTPException(status_code=403, detail="Verification token mismatch.")

@app.post("/webhook")
async def receive_webhook(request: Request):
    try:
        payload = await request.json()
        # Example of navigating the payload; adjust according to your actual structure.
        await process_event(payload, app.state.redis)
        
        # Respond to WhatsApp with a simple success acknowledgment (200 OK)
        return JSONResponse(content={"status": "200",})
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))


