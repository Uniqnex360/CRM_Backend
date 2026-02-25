from pydantic import BaseModel, EmailStr,Field
from typing import Optional, List
from datetime import datetime


class LeadBase(BaseModel):
    # domain: Optional[str] = None
    company_id: Optional[str] = None
    company_name:Optional[str]=None
    name: str  
    title: Optional[str] = None
    email_id: Optional[EmailStr] = None
    source: Optional[str] = None
    source_link: Optional[str] = None
    hq_no: Optional[str] = None
    direct_no: Optional[str] = None
    vertical: Optional[str] = None
    sub_category: Optional[str] = None
    product_count: Optional[int] = None
    emp_size: Optional[int] = None
    revenue: Optional[int] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    type: Optional[str] = None
    cms: Optional[str] = None
    ecommerce: Optional[str] = None
    site_search: List[str] = Field(default_factory=list)

class LeadCreate(LeadBase):
    pass



class LeadResponse(LeadBase):
    id:str
    domain: Optional[str] = None
    company_name: Optional[str] = None
    name: str  
    title: Optional[str] = None
    company_id:Optional[str]
    created_at: Optional[datetime] = None
    is_active: bool = True
    added_to_favourites: bool = False



class LeadUpdate(BaseModel):
    # domain: Optional[str] = None
    # company_name: Optional[str] = None
    name: Optional[str]=None 
    title: Optional[str] = None
    email_id: Optional[EmailStr] = None
    source: Optional[str] = None
    source_link: Optional[str] = None
    hq_no: Optional[str] = None
    direct_no: Optional[str] = None
    vertical: Optional[str] = None
    sub_category: Optional[str] = None
    product_count: Optional[int] = None
    emp_size: Optional[int] = None
    revenue: Optional[int] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    type: Optional[str] = None
    cms: Optional[str] = None
    ecommerce: Optional[str] = None
    site_search: Optional[List[str]] = Field(default_factory=list)
    company_name:Optional[str]=None