from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    tenant_id: Optional[str] = None
   
    role: Optional[str] = "user" 

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
    org_name: str
    location:Optional[str]=None
    industry:Optional[str]=None
    domain_url:Optional[str]=None



class AdminCompanyResponse(AdminCompanyBase):
    id: str
    created_by: str
  
