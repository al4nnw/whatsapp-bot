
from pydantic import BaseModel


class Media(BaseModel):
  id: int
  media_type: str
  mime_type: str