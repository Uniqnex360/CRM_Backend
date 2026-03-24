from pydantic import BaseModel, EmailStr,Field,ConfigDict,validator
from typing import Optional, List,Literal
from datetime import datetime
from bson import ObjectId

class TemplateCreate(BaseModel):
    template_name: str
    description: Optional[str] = None
    subject: Optional[str] = None
    body: str

class TemplateUpdate(BaseModel):
    template_name: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None

class TemplateResponse(TemplateCreate):
    id: str
    created_at: datetime
