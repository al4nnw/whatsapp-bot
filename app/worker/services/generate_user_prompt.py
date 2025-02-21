from app.contracts.chat_session import ChatSession
from app.contracts.media import Media
from app.utils.sanitize_input import sanitize_input
from app.worker.services.get_media_url import get_media_url
from app.worker.services.retrieve_file import retrieve_file
from app.worker.services.transcribe_audio import transcribe_audio


async def generate_user_prompt(session: ChatSession) -> str:
    # Based on the type of messages, take an action
    compiled_prompt = []
    for message in session.queue_user_messages:
      if message["type"] == "text":
        compiled_prompt.append(sanitize_input(message["text"]["body"]))
        
      elif message["type"] == "audio":
        compiled_prompt.append("User audio message:")
        audio = Media(
          id=message["audio"]["id"],
          mime_type=message["audio"]["mime_type"],
          media_type="audio"
        )
        
        file_url = await get_media_url(audio)
        file_name = f"{session.user_id}/audios/{audio.id}"
        path = await retrieve_file(file_url, file_name)        
        print(f"Media saved to {path.resolve()}") 
        
        transcript = await transcribe_audio(path)      
        compiled_prompt.append(sanitize_input(transcript))

      elif message["type"] == "image":
        image = Media(
          id=message["image"]["id"],
          mime_type=message["image"]["mime_type"],
          media_type="image"
        )
        
        caption = message["image"]["caption"]
        
        file_url = await get_media_url(image)
        file_name = f"{session.user_id}/images/{image.id}"
        path = await retrieve_file(file_url, file_name)
        file_path = path.resolve()
        print(f"Media saved to {file_path}") 
        compiled_prompt.append("###IMAGE_DOWNLOADED###" + file_path)
        compiled_prompt.append("Legenda da imagem: " + sanitize_input(caption))
    
    return "\n".join(compiled_prompt)