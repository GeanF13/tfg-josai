from pydantic import BaseModel

class ChatRequest(BaseModel):
    subject_id: str
    user_query: str
