from pydantic import BaseModel, Field
from typing import List, Optional
import uuid

class ComposeRequest(BaseModel):
    query: str = Field(..., description="User query")
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class FeedbackRequest(BaseModel):
    trace_id: str = Field(..., description="Trace ID from compose response")
    feedback: str = Field(..., description="User feedback")

class Citation(BaseModel):
    source: str
    snippet: str

class ComposeResponse(BaseModel):
    final_text: str
    citations: List[Citation]
    audio_url: str
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))