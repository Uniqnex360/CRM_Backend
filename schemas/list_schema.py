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

class ListUpdate(ListBase):
    list_name:str
    description:Optional[str]=None
    type:ListType

class ListResponse(ListBase):
    id: str
    owner_id: str
    no_of_records: int
    created_at: datetime
    updated_at: datetime


class ListMemberCreate(BaseModel):
    entity_ids: List[str] 