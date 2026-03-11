from pydantic import BaseModel, EmailStr,Field,ConfigDict
from typing import Optional, List
from datetime import datetime

from bson import ObjectId

class CompanyBase(BaseModel):
    company_name:str
    domain_url:Optional[str]=None
    company_linkedin_source: Optional[str] = None
    employee_size: Optional[str] = None
    city:Optional[str]=None
    state:Optional[str]=None
    country: Optional[str] = None
    amazon_existing:Optional[bool]=None
    gross_revenue:Optional[str]=None
    industry:Optional[str]=None
    founding_year: Optional[str] = None
    owner_id: str | None = None 

class CompanyCreate(CompanyBase):
     pass 



class CompanyUpdate(BaseModel):
    company_name:Optional[str]=None
    domain_url:Optional[str]=None
    company_linkedin_source: Optional[str] = None
    employee_size: Optional[str] = None
    country: Optional[str] = None
    amazon_existing:Optional[bool]=None
    gross_revenue:Optional[str]=None
    industry:Optional[str]=None
    founding_year: Optional[str] = None


class LeadMini(BaseModel):
    id: str
    name: Optional[str] = None
    primary_number: Optional[str] = None
    title: Optional[str] = None
    personal_linkedin_source: Optional[str] = None
    # email_id:Optional[str]=None

class CompanyResponse(CompanyBase):

    id:str=Field(alias="_id")
    owner_id: str | None = None  
    created_at: Optional[datetime] = None
    is_active: bool = True
    added_to_favourites: bool = False
    leads: Optional[List[LeadMini]] = []
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
class CompanyStatus(BaseModel):
    is_active:Optional[bool]=None
    added_to_favourites:Optional[bool]=None