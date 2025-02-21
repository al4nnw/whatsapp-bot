import os
import aiohttp
from app.contracts.media import Media

ACCESS_TOKEN = os.getenv("WHATSAPP_TOKEN")

async def get_media_url(media: Media) -> str:
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    async with aiohttp.ClientSession() as aio_req:
        url = f"https://graph.facebook.com/v22.0/{media.id}/"
        async with aio_req.get(url, headers=headers) as response:
            response_status = response.status
            if response_status != 200:
                return (f"Failed to retrieve media URL. Status code: {response_status}")
            
            data = await response.json()
    media_url = data.get("url")
    if not media_url:
        raise Exception("Failed to retrieve media URL.")
    print(f"Media URL: {media_url}")
    return media_url

