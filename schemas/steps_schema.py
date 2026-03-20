from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, field_validator, Field
from typing import Optional
from pydantic import ConfigDict

class StepCreate(BaseModel):
    sequence_id: str
    step_type: str
    delay_in_days: Optional[int] = 0
    delay_in_minutes: Optional[int] = 0
    subject: Optional[str] = None
    body: Optional[str] = None

    def get_total_delay_minutes(self):
        return (self.delay_in_days or 0) * 1440 + (self.delay_in_minutes or 0)

class StepResponse(BaseModel):
    id: str = Field(alias="_id")
    sequence_id: str
    step_type: str
    delay_in_minutes: int
    subject: Optional[str] = None
    body: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )