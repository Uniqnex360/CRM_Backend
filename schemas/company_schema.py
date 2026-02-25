from pydantic import BaseModel, EmailStr,Field
from typing import Optional, List
from datetime import datetime



class CompanyBase(BaseModel):
    company_name: str
    domain:Optional[str]=None
    company_link: Optional[str] = None
    company_email:Optional[EmailStr]=None
    description: Optional[str] = None
    employees_count: Optional[int] = None
    city: Optional[str] = None
    country: Optional[str] = None
    links: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    revenue: Optional[str] = None
    founded: Optional[str] = None
    contact: Optional[str] = None

class CompanyCreate(CompanyBase):
     pass 



class CompanyUpdate(BaseModel):
    company_name:Optional[str]=None
    domain:Optional[str]=None
    company_link: Optional[str] = None
    company_email:Optional[EmailStr]=None
    description: Optional[str] = None
    employees_count: Optional[int] = None
    city: Optional[str] = None
    country: Optional[str] = None
    links: Optional[List[str]] = Field(default_factory=list)
    keywords: Optional[List[str]] = Field(default_factory=list)
    revenue: Optional[str] = None
    founded: Optional[str] = None
    contact: Optional[str] = None

class CompanyResponse(CompanyBase):
    id:str
    company_name: str
    domain:Optional[str]=None
    company_link: Optional[str] = None
    company_email:Optional[EmailStr]=None
    description: Optional[str] = None
    employees_count: Optional[int] = None
    city: Optional[str] = None
    country: Optional[str] = None
    links: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    revenue: Optional[str] = None
    founded: Optional[str] = None
    contact: Optional[str] = None
     
    created_at: Optional[datetime] = None
    is_active: bool = True
    added_to_favourites: bool = False

    
    
class CompanyStatus(BaseModel):
    is_active:Optional[bool]=None
    added_to_favourites:Optional[bool]=None