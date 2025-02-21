from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field

from app.contracts.media import Media

class ChatSession(BaseModel):
    user_id: int = Field(default_factory=int, description="Unique user identifier")
    last_message_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),
                                         description="Timestamp of last message in the session")
    queue_user_messages: list[dict] = Field(default_factory=list,
                                     description="List of messages sent by the user")
    bot_messages: list[str] = Field(default_factory=list,
                                    description="List of responses from the bot")
    ttl_seconds: int = Field(default_factory=int,
                             description="TTL of this chat session in seconds")
    joined_user_messages: list[str] = Field(default_factory=list,
                                     description="Joined user messages")
    
    @property
    def last_message_sent_less_than_one_minute_ago(self):
        return self.last_message_time > datetime.now(timezone.utc) - timedelta(minutes=1)
    
    
    @property
    def has_user_messages(self):
        return len(self.queue_user_messages) > 0


    def clean_user_messages(self):
        self.queue_user_messages = []