from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from bson import ObjectId

class SequenceStepCreate(BaseModel):
    sequence_id: str
    step_order: int
    step_type: str  
    delay_in_days: int
    subject: Optional[str] = None
    body: Optional[str] = None


class SequenceStepResponse(BaseModel):
    id: str = Field(alias="_id")
    sequence_id: str
    step_order: int
    step_type: str
    delay_in_days: int
    subject: Optional[str] = None
    body: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )