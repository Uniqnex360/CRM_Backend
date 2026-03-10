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
from fastapi_pagination import Page,paginate
from fastapi_pagination.ext.motor import paginate   


from services.create_or_import import create_single_lead,import_leads_from_file

from auth.create_access import get_current_user
from schemas.lead_schema import LeadCreate,LeadBase,LeadResponse,LeadUpdate,Leadstatus
from utils.company_resolve import resolve_company
from utils.custom_pagination import CustomParams
from utils.clean_data import normalize_text,normalize_regex_title,normalize_fuzzy_regex,normalize_fuzzy_regex_safe,normalize_sort,location_regex
from pymongo import ASCENDING, DESCENDING
import re
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

ALLOWED_SORT_FIELDS = ["name", "title", "industry", "company"]

SORT_FIELD_MAP = {
    "name": "name",
    "title": "title",
    "industry": "industry",
    "company": "company_name"
}
async def transform_leads(items):
    
        result = []
        company_ids = [
        ObjectId(lead["company_id"])
        for lead in items
        if lead.get("company_id")
    ]

        companies = await database.company.find(
        {"_id": {"$in": company_ids}}
    ).to_list(None)

        company_map = {str(c["_id"]): c["company_name"] for c in companies}


        for lead in items:

            lead["_id"] = str(lead["_id"])

            company_id = lead.get("company_id")

            if company_id:
                lead["company_id"] = str(company_id)
                lead["company_name"] = company_map.get(str(company_id))
            else:
                lead["company_name"] = None
            lead["industry"] = lead.get("industry") or ""

            result.append(lead)
        return result
   
@leads_router.get("/read_leads", response_model=Page[LeadResponse])
async def get_all_leads(
    params:CustomParams=Depends(),
    keyword: str = None,
    location:str=None,
    title:str=None,
    company:str=None,
    industry:str=None,
    current_user=Depends(get_current_user)
):

    query = {}
    if keyword:

        keyword_regex =normalize_regex_title(keyword)
        print("keyword: ",keyword_regex)
        parts = [p.strip().lower() for p in  re.split(r"[,\s]+", keyword) if p.strip() ]
        print(parts)
        query["$or"]=[
            {"name": {"$regex": keyword_regex, "$options": "i"}},
            {"title": {"$regex":  keyword_regex, "$options": "i"}},
            {"industry": {"$regex":  keyword_regex, "$options": "i"}},
            {"country": {"$regex":  keyword_regex, "$options": "i"}},
            {"city":{"$regex":keyword_regex,"$options":"i"}},
            {"domain_url":{"$regex": keyword_regex,"$options":"i"}},
        
            {"email_id":{"$regex": keyword_regex,"$options":"i"}},
            {"primary_number":{"$regex": keyword_regex,"$options":"i"}},
          ]
        if len(parts) >= 2:
              city = location_regex(parts[0])
              country = location_regex(parts[1])

              print("city:", city)
              print("country:", country)
              query["$or"].append({
            "$and": [
                {"city": {"$regex": city, "$options": "i"}},
                {"country": {"$regex": country, "$options": "i"}}]})

        company_match= await database.company.find_one(
            {"company_name": {"$regex": keyword, "$options": "i"}}
        )
        if company_match:
           query["$or"].append({"company_id": company_match["_id"]})
    
    filter=[]
    if location and location.strip():

      parts = [p.strip() for p in re.split(r"[,\s]+", location) if p.strip()]
      print("parts:", parts)
      if len(parts) == 1:

        word = location_regex(parts[0])
        print(word)

        filter.append({
            "$or": [
                {"city": {"$regex": word, "$options": "i"}},
                {"country": {"$regex": word, "$options": "i"}}
            ]})
      elif len(parts) == 2:

        city = location_regex(parts[0])
        country = location_regex(parts[1])

        filter.append({
            "$and": [
                {"city": {"$regex": city, "$options": "i"}},
                {"country": {"$regex": country, "$options": "i"}}
            ]
        })
        
    if title and title.strip():
       title = normalize_fuzzy_regex_safe(title)
       print(title)
       filter.append({
           "title": {"$regex": title, "$options": "i"}})
       

    if industry and industry.strip():
           industry = normalize_fuzzy_regex(industry)
           print(industry)
        #    industry = normalize_text(industry)
        #    industry = ".*".join(list(industry))
           filter.append({
        "industry": {"$regex": industry, "$options": "i"}})
           
    if company:
       company_regex = normalize_fuzzy_regex(company)
    #    company_regex=".*".join(list(company_regex))

       company_doc = await database.company.find(
        {"company_name": {"$regex": company_regex, "$options": "i"}}
    ).to_list(None)

       if company_doc:
           company_ids = [c["_id"] for c in company_doc]
           filter.append({
            "company_id": {"$in": company_ids}
        })

    if filter:
      if "$or" in query:
        query = {"$and": [query] + filter}
      else:
        query = {"$and": filter}
    
    sort_by = params.sort_by.lower() if params.sort_by else "name"
    sort_order = params.sort_order.lower() if params.sort_order else "asc" 
    items = await database.leads.find(query).to_list(None)
    items = await transform_leads(items)  

    if sort_by == "company": 
      items = sorted(
        items,
        key=lambda x: (x.get("company_name") or "").lower(),
        reverse=(sort_order == "desc")
    )
      from fastapi_pagination import paginate
 
      page_result = paginate(items, params)
    else:
      if sort_by not in ALLOWED_SORT_FIELDS:
          sort_by = "name"

      sort_direction = 1 if sort_order.lower() == "asc" else -1
    
      sort_field = SORT_FIELD_MAP[sort_by]
      from fastapi_pagination.ext.motor import paginate  
      page_result = await paginate(
    database.leads,
    query,
    params=params,
    sort=[(sort_field, sort_direction)],
    transformer=transform_leads
)
    if params.page > page_result.pages and page_result.pages > 0:
        params.page = page_result.pages
        if sort_by ==company:
              page_result=paginate(items,params)
        else:
          page_result = await paginate(database.leads, query, params=params, transformer=transform_leads,sort=[(sort_field, sort_direction)],)
      

    return page_result




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
    for key, value in lead.items():
      if isinstance(value, ObjectId):
        lead[key] = str(value)


    return lead


@leads_router.put("/update_leads/{lead_id}", response_model=LeadResponse)
async def update_leads(
    lead_id: str,
    lead_update: LeadUpdate,
    current_user=Depends(get_current_user)
):
    try:
        object_id = ObjectId(lead_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid lead ID format")

    existing_lead = await database.leads.find_one({
        "_id": object_id,
        "owner_id": str(current_user["_id"])
    })

    if not existing_lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Convert model to dict and remove None values
    update_fields = {
        k: v for k, v in lead_update.dict().items()
        if v is not None
    }

    if not update_fields:
        raise HTTPException(status_code=400, detail="No valid field to update")


    if "company_id" in update_fields or "company_name" in update_fields:

        company_id = await resolve_company(
            company_id=update_fields.get("company_id"),
            company_name=update_fields.get("company_name")
        )

        update_fields["company_id"] = company_id
        update_fields.pop("company_name", None)

    update_fields["updated_at"] = datetime.utcnow()

    await database.leads.update_one(
        {"_id": object_id},
        {"$set": update_fields}
    )

    updated_lead = await database.leads.find_one({"_id": object_id})

    updated_lead["id"] = str(updated_lead["_id"])
    del updated_lead["_id"]

    return updated_lead



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
 

      updated_leads=await database.leads.find_one_and_update(
                {"_id": object_id,"owner_id": str(current_user["_id"])},
               {"$set": update_fields},
         return_document=ReturnDocument.AFTER
           )

      if not updated_leads:
           raise HTTPException(status_code=404, detail="Lead not found")

      updated_leads["id"] = str(updated_leads["_id"])
      del updated_leads["_id"]
      for k, v in updated_leads.items():
        if isinstance(v, ObjectId):
            updated_leads[k] = str(v)

      return updated_leads
       