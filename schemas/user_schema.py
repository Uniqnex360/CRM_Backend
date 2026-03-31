from pydantic import BaseModel, EmailStr
from typing import Optional
from pydantic import field_validator
from bson import ObjectId

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    # tenant_id: Optional[str] = None
   
    role: Optional[str] = "user" 

class UserResponse(BaseModel):
   
    id: str
    name: str
    email: EmailStr
    tenant_id: Optional[str] = None
    role:Optional[str]=None
  

    @field_validator("tenant_id", mode="before")
    def convert_objectid(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v

class UserUpdate(BaseModel):
    name: str
    email: EmailStr
    password:str
    tenant_id: Optional[str] = None
    role: Optional[str] = None

class AdminCompanyBase(BaseModel):
    org_name: str
    location:Optional[str]=None
    industry:Optional[str]=None
    domain_url:Optional[str]=None

class AssignCompanyRequest(BaseModel):
    tenant_id: str 

class AdminCompanyResponse(AdminCompanyBase):
    id: str
    created_by: str
  
