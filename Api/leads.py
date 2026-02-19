from fastapi import APIRouter,HTTPException,Depends
from datetime import datetime
from bson import ObjectId
from database import database

from bson.errors import InvalidId

from Auth.create_access import get_current_user
from schemas.lead_schema import LeadCreate,LeadBase,LeadResponse

leads_router=APIRouter(prefix="/leads",tags=['Leads'])


@leads_router.post("/create_leads", response_model=LeadResponse)
async def create_lead(
    lead: LeadCreate,
    current_user=Depends(get_current_user)
):
    

    if not lead.email_id and not lead.direct_no:
        raise HTTPException(
            status_code=400,
            detail="Either email_id or direct_no is required"
        )

    lead_dict = lead.dict()
    lead_dict["owner_id"] = str(current_user["_id"])
    lead_dict["created_at"] = datetime.utcnow()
    lead_dict["added_to_favourites"] = False

    lead_dict["is_active"] = True

    result = await database.leads.insert_one(lead_dict)
    new_lead = await database.leads.find_one({"_id": result.inserted_id})

    new_lead["id"] = str(new_lead["_id"])
    return new_lead 

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