from pydantic import BaseModel, EmailStr,Field,ConfigDict,validator
from typing import Optional, List,Literal
from datetime import datetime
from bson import ObjectId
from pydantic import field_validator

class TemplateCreate(BaseModel):
    template_name: str
    description: Optional[str] = None
    subject: Optional[str] = None
    body: str
    industry_id: Optional[str] = None   
    @field_validator("industry_id", mode="before")
    def validate_industry_id(cls, v):
        if v:
            return str(v)
        return v
class TemplateUpdate(BaseModel):
    template_name: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    industry_id: Optional[str] = None   

class TemplateResponse(TemplateCreate):
    id: str
    created_at: datetime
    industry_id: Optional[str] = None  
