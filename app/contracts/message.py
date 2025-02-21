from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# Base model with common fields
class MessageBase(BaseModel):
    from_: str = Field(..., alias="from")
    id: str
    timestamp: str
    type: str

# 1. Text Message
class TextContent(BaseModel):
    body: str

class TextMessage(MessageBase):
    type: Literal["text"] = "text"
    text: TextContent

# 2. Image Message
class ImageContent(BaseModel):
    mime_type: str
    sha256: str
    id: str

class ImageMessage(MessageBase):
    type: Literal["image"] = "image"
    image: ImageContent

# 3. Audio Message
class AudioContent(BaseModel):
    mime_type: str
    sha256: str
    id: str

class AudioMessage(MessageBase):
    type: Literal["audio"] = "audio"
    audio: AudioContent

# 4. Video Message
class VideoContent(BaseModel):
    mime_type: str
    sha256: str
    id: str

class VideoMessage(MessageBase):
    type: Literal["video"] = "video"
    video: VideoContent

# 5. Document Message
class DocumentContent(BaseModel):
    mime_type: str
    sha256: str
    id: str
    filename: str

class DocumentMessage(MessageBase):
    type: Literal["document"] = "document"
    document: DocumentContent

# 6. Sticker Message
class StickerContent(BaseModel):
    mime_type: str
    sha256: str
    id: str

class StickerMessage(MessageBase):
    type: Literal["sticker"] = "sticker"
    sticker: StickerContent

# 7. Location Message
class LocationContent(BaseModel):
    latitude: float
    longitude: float
    name: Optional[str] = None
    address: Optional[str] = None

class LocationMessage(MessageBase):
    type: Literal["location"] = "location"
    location: LocationContent

# 8. Contacts Message
class ContactProfile(BaseModel):
    name: str

class Contact(BaseModel):
    profile: ContactProfile
    wa_id: str

class ContactsMessage(MessageBase):
    type: Literal["contacts"] = "contacts"
    contacts: List[Contact]

# 9. Interactive Message - Button Reply
class ButtonReply(BaseModel):
    id: str
    title: str

class InteractiveButtonContent(BaseModel):
    type: Literal["button_reply"] = "button_reply"
    button_reply: ButtonReply

class InteractiveButtonMessage(MessageBase):
    type: Literal["interactive"] = "interactive"
    interactive: InteractiveButtonContent

# 10. Interactive Message - List Reply
class ListReply(BaseModel):
    id: str
    title: str

class InteractiveListContent(BaseModel):
    type: Literal["list_reply"] = "list_reply"
    list_reply: ListReply

class InteractiveListMessage(MessageBase):
    type: Literal["interactive"] = "interactive"
    interactive: InteractiveListContent

# Example usage:
if __name__ == "__main__":
    sample_text = {
        "from": "1234567890",
        "id": "wamid.ID1",
        "timestamp": "1640995200",
        "type": "text",
        "text": {"body": "Hello, this is a text message."}
    }
    
    text_msg = TextMessage.parse_obj(sample_text)
    print(text_msg.json(by_alias=True, indent=2))
