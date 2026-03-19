from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SequenceBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_template: bool = False
    is_active: bool = True
  

class CreateSequence(SequenceBase):
    pass

class SequenceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    
class SequenceStatus(BaseModel):  
    is_active: bool
   

class SequenceResponse(SequenceBase):
    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime


#sequence step
class StepCreate(BaseModel):
    sequence_id:str
    step_number:int
    delay_minutes:int=0
    subject:str
    body:str

class SequenceStepResponse(StepCreate):
    id:str
    created_at:datetime

