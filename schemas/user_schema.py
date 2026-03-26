from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    tenant_id: Optional[str] = None
    role:str 

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    tenant_id: Optional[str] = None
    role:str

class UserUpdate(BaseModel):
    name: str
    email: EmailStr
    password:str
    tenant_id: Optional[str] = None
    role: Optional[str] = None

class AdminCompanyBase(BaseModel):
    name: str

class AdminCompanyResponse(AdminCompanyBase):
    id: str
    created_by: str
  
