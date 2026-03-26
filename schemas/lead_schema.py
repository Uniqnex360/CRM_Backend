from pydantic import BaseModel, EmailStr,Field,ConfigDict,validator
from typing import Optional, List
from datetime import datetime
from bson import ObjectId



class LeadBase(BaseModel):
        name:str
        email_id:EmailStr
        month:Optional[str]=None	
        date:Optional[str]=None		
        industry:Optional[str]=None		
        company_id: Optional[str] = None
        company_name:str		
        domain_url:Optional[str]=None		
        company_linkedin_source:Optional[str]=None	 
        source:Optional[str]=None
        personal_linkedin_source: Optional[str] = None		
        title:Optional[str]=None
        primary_number:Optional[str]=None
        address:Optional[str]=None 	
        city:Optional[str]=None	
        state:Optional[str]=None	
        country: Optional[str] = None
        location:Optional[str]=None #city and country
        founding_year:Optional[str]=None 	
        gross_revenue:Optional[str]=None		
        employee_size:Optional[str]=None 		
        amazon_existing:Optional[str]=None 				
        sub_category:Optional[str]=None 		
        product_count:Optional[str]=None 		
        cms:Optional[str]=None 
        keywords:Optional[list[str]]=None
        is_global: Optional[bool] = False  #global data
        tenant_id: Optional[str] = None
class LeadCreate(LeadBase):
        pass	

class LeadResponse(LeadBase):
    tenant_id: Optional[str] = None
    id:Optional[str]=Field(alias="_id")
    domain: Optional[str] = None
    company_name: Optional[str] = None
    email_id:Optional[EmailStr]=None
    name:Optional[str]=None
    title: Optional[str] = None
    company_id:Optional[str]=None
    created_at: Optional[datetime] = None
    is_active: bool = True
    added_to_favourites: bool = False
    is_global: Optional[bool] = False #global data
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    @validator("id", "company_id", pre=True, always=True)
    def objectid_to_str(cls, v):
        if isinstance(v, ObjectId):
               return str(v)
        return v
class LeadUpdate(BaseModel):
        name:Optional[str]=None
        email_id:Optional[EmailStr]=None
        month:Optional[str]=None	
        date:Optional[str]=None		
        industry:Optional[str]=None		
        company_name:Optional[str]=None
        company_id: Optional[str] = None		
      	 
        domain_url:Optional[str]=None		
        company_linkedin_source:Optional[str]=None	 
        source:Optional[str]=None		
        title:Optional[str]=None
        role:Optional[str]=None		
        personal_linkedin_source:Optional[str]=None
        primary_number:Optional[str]=None
        hq_no:Optional[str]=None
        address:Optional[str]=None 	
        city:Optional[str]=None	
        state:Optional[str]=None	
        country: Optional[str] = Field(None, validation_alias="Geo")
        founding_year:Optional[str]=None 		
        gross_revenue:Optional[str]=None 		
        employee_size:Optional[str]=None 		
        amazon_existing:Optional[str]=None 		
        vertical:Optional[str]=None 
        revenue:Optional[str]=None		
        sub_category:Optional[str]=None 		
        product_count:Optional[str]=None 		
        cms:Optional[str]=None 
class Leadstatus(BaseModel):
    is_active:Optional[bool]=None
    added_to_favourites:Optional[bool]=None


