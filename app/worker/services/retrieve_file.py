import os
from pathlib import Path
import aiohttp
import aiofiles

ACCESS_TOKEN = os.getenv("WHATSAPP_TOKEN")

async def retrieve_file(file_url: str, file_name: str) -> Path:
    
    if (Path(file_name).exists()):
        print(f"File already exists at {file_name}")
        return Path(file_name)
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url, headers=headers) as response:
            if response.status != 200:
                print(f"Failed to retrieve file. Status code: {response.status}")
                return
            
            # Determine file extension if not provided
            content_type = response.headers.get("Content-Type", "")
            print(f"Debug: Retrieved content type: {content_type}")
            ext = content_type.split("/")[1]
            print(f"Debug: Retrieved extension: {ext}")
            
            # If ext is None, log a warning and set ext to empty string
            if ext is None:
                print("Warning: Unable to determine file extension; using empty extension.")
                ext = ""
            
            print(f"Debug: Final file name before saving: {file_name + ext}")
            file_name = file_name + "." + ext
            
            # Create directory if it doesn't exist
            dir_name = os.path.dirname(file_name)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)
            
            # Stream and save the file in chunks
            async with aiofiles.open(file_name, 'wb') as out_file:
                async for chunk in response.content.iter_chunked(1024):
                    await out_file.write(chunk)
            
            print(f"File saved as {file_name}")
            
            return Path(file_name)
