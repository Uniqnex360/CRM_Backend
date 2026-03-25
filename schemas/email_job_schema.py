from pydantic import BaseModel, field_serializer
from typing import Optional,Dict,Any
from datetime import datetime
from enum import Enum

class EmailStatus(str, Enum):
    pending = "pending"
    sent = "sent"
    delivered = "delivered" 
    failed = "failed"

class EmailJobBase(BaseModel):
    sequence_id: str
    schedule_id: str
    email: str
    user_id: str


class CreateEmailJob(EmailJobBase):
    scheduled_at: datetime


class EmailJobResponse(EmailJobBase):
    id: str
    status: EmailStatus
    scheduled_at: datetime
    sent_at: Optional[datetime] = None
    created_at: datetime

    message_id: Optional[str] = None   
    opened: Optional[bool] = False
    opened_at: Optional[datetime] = None
    click_count: Optional[int] = 0
    last_clicked_at: Optional[datetime] = None
    brevo_raw: Optional[Dict[str, Any]] = None

    @field_serializer("scheduled_at", "sent_at", "created_at")
    def format_datetime(self, value: Optional[datetime]):
        if value:
            return value.strftime("%Y-%m-%d %H:%M")
        return value