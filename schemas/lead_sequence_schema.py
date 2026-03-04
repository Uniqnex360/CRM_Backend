from pydantic import BaseModel,Field,ConfigDict
from typing import Optional
from datetime import datetime
from bson import ObjectId

class LeadSequenceCreate(BaseModel):
    lead_id: str
    sequence_id: str

class LeadSequenceResponse(BaseModel):
    id: str = Field(alias="_id")
    lead_id: str
    sequence_id: str
    current_step: int
    next_run_at: datetime
    status: str 
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )