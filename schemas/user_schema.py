from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    company_id: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    company_id: str
    role:str

class UserUpdate(BaseModel):
    name: str
    email: EmailStr
    password:str
    company_id: Optional[str] = None
    role: Optional[str] = None
