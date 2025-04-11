from pydantic import BaseModel
from typing import Optional
class ChatRequest(BaseModel):
    subject_id: str
    user_query: str
    thread_id: Optional[str] = None
