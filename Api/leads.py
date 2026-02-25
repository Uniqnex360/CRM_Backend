import json
from fastapi import UploadFile, File, Form
from typing import Optional
from fastapi import APIRouter,HTTPException,Depends
from datetime import datetime
from bson import ObjectId
from database import database
from pydantic import BaseModel
from bson.errors import InvalidId
from pymongo import ReturnDocument
from services.create_or_import import create_single_lead,import_leads_from_file

from Auth.create_access import get_current_user
from schemas.lead_schema import LeadCreate,LeadBase,LeadResponse,LeadUpdate

leads_router=APIRouter(prefix="/leads",tags=['leads'])



@leads_router.post("/create_leads")
async def create_lead(
    lead: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user=Depends(get_current_user)
):

    if file:
        return await import_leads_from_file(
            file,
            current_user,
            database
        )

    if lead:
        try:
            lead_data = json.loads(lead)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON format")

        return await create_single_lead(
            lead_data,
            current_user,
            database
        )
    raise HTTPException(
        status_code=400,
        detail="Provide either lead JSON or file upload"
    )



@leads_router.get("/read_leads")
async def get_all_leads(
    keyword: str = None,
    vertical: str = None,
    current_user=Depends(get_current_user)
):
    query = {"owner_id": str(current_user["_id"])}

    if keyword:
        query["site_search"] = {"$in": [keyword]}

    if vertical:
        query["vertical"] = vertical

    leads = []
    async for lead in database.leads.find(query):
        lead["id"] = str(lead["_id"])
        del lead['_id']
        leads.append(lead)

    return leads


@leads_router.get("/read_leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    current_user=Depends(get_current_user)
):
    try:
        object_id = ObjectId(lead_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid lead ID format")

    lead = await database.leads.find_one({
        "_id": object_id,
        "owner_id": str(current_user["_id"])
    })

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead["id"] = str(lead["_id"])
    del lead["_id"]

    return lead


@leads_router.put("/update_leads/{lead_id}",response_model=LeadResponse)
async def update_leads(lead_id:str,lead_update:LeadUpdate,current_user=Depends(get_current_user)):
    try:
        object_id=ObjectId(lead_id)
    except:
        raise HTTPException(status_code=400,detail="Invalid lead ID format")
    
    existing_lead = await database.leads.find_one({
        "_id": object_id,
        "owner_id": str(current_user["_id"])})
    if not existing_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    
    update_data = {k: v for k, v in lead_update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400,detail="No valid field")
    update_data["updated_at"]=datetime.utcnow()
  
    await database.leads.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )

    lead = await database.leads.find_one({"_id": object_id})
    lead["id"] = str(lead["_id"])
    return lead


class Leadstatus(BaseModel):
    is_active:Optional[bool]=None
    added_to_favourites:Optional[bool]=None

@leads_router.patch("/leads_status/{lead_id}",response_model=LeadResponse)
async def leads_status(lead_id:str,
                       status_update:Leadstatus,
                       current_user=Depends(get_current_user)):
      try:
        object_id=ObjectId(lead_id)
      except:
          raise HTTPException(status_code=400,detail="Invalid lead ID format")
       
      lead = await database.leads.find_one({
        "_id": object_id,
        "owner_id": str(current_user["_id"])})
      if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
      

      update_fields = {k: v for k, v in status_update.dict().items() if v is not None}
 

      updated_leads=await database.company.find_one_and_update(
                {"_id": object_id},
               {"$set": update_fields},
         return_document=ReturnDocument.AFTER
           )

      if not updated_leads:
           raise HTTPException(status_code=404, detail="Company not found")

      updated_leads["id"] = str(updated_leads["_id"])
      del updated_leads["_id"]

      return updated_leads
       