from pydantic import BaseModel, EmailStr,Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ListType(str,Enum):
    people="people"
    companies="companies"


class ListBase(BaseModel):
    list_name:str
    description:Optional[str]=None
    type:ListType

class ListCreate(ListBase):
    pass

class ListUpdate(BaseModel):
    list_name:str
    description:Optional[str]=None
    

class ListResponse(ListBase):
    id: str
    owner_id: str
    no_of_records: int
    created_at: datetime
    updated_at: datetime


class ListMemberCreate(BaseModel):
    entity_ids: Optional[List[str]] = []
    keyword: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None

class RemoveListMembers(BaseModel):
    entity_id: Optional[str] = None
    entity_ids: Optional[List[str]] = None

class PersonMember(BaseModel):
    id: str
    name: Optional[str]
    title: Optional[str]
    company_name: Optional[str]

class CompanyMember(BaseModel):
    id: str
    company_name: Optional[str]
    industry: Optional[str]
    domain_url: Optional[str]

class ListWithMembersResponse(ListResponse):
    people: Optional[List[PersonMember]] = []
    companies: Optional[List[CompanyMember]] = []