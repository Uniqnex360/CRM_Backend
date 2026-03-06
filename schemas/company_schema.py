from pydantic import BaseModel, EmailStr,Field,ConfigDict
from typing import Optional, List
from datetime import datetime

from bson import ObjectId

class CompanyBase(BaseModel):
    company_name:str
    domain:Optional[str]=None
    url:Optional[str]=None
    company_linkedin_source: Optional[str] = None
    headcount:Optional[str]=None
    employee_size: Optional[str] = None
    geo: Optional[str] = None
    country: Optional[str] = None
    amazon_existing:Optional[bool]=None
    revenue: Optional[str] = None
    gross_revenue:Optional[str]=None
    industry:Optional[str]=None
    vertical:Optional[str]=None
    founding_year: Optional[str] = None

class CompanyCreate(CompanyBase):
     pass 



class CompanyUpdate(BaseModel):
    company_name:Optional[str]=None
    domain:Optional[str]=None
    url:Optional[str]=None
    company_linkedin_source: Optional[str] = None
    headcount:Optional[str]=None
    employee_size: Optional[str] = None
    geo: Optional[str] = None
    country: Optional[str] = None
    amazon_existing:Optional[bool]=None
    revenue: Optional[str] = None
    gross_revenue:Optional[str]=None
    industry:Optional[str]=None
    vertical:Optional[str]=None
    founding_year: Optional[str] = None

class CompanyResponse(CompanyBase):
    id:str=Field(alias="_id")
     
    created_at: Optional[datetime] = None
    is_active: bool = True
    added_to_favourites: bool = False

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
class CompanyStatus(BaseModel):
    is_active:Optional[bool]=None
    added_to_favourites:Optional[bool]=None