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
from utils.clean_data import normalize_fuzzy_regex_safe
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

ALLOWED_SORT_FIELDS = ["name", "title", "industry", "company","location"]


SORT_FIELD_MAP = {
    "name": "name",
    "title": "title",
    "industry": "industry",
    "company": "company_name",
    "location":"location"
}


@leads_router.get("/read_leads", response_model=Page[LeadResponse])
async def get_all_leads(
    params: CustomParams = Depends(),
    keyword: str = None,
    name: str = None,
    location: str = None,
    title: str = None,
    company: str = None,
    industry: str = None,
    current_user=Depends(get_current_user)
):
    user_id = str(current_user["id"])
    user_company_id = current_user.get("user_company_id")
    if current_user["role"] == "super_admin":
           access_filter = {} 
    else:   
       access_filter = {
    "$or": [
        {"owner_id": user_id},                  
        # {"company_id": user_company_id} ,
        {"tenant_id": str(current_user["tenant_id"])},
        {"is_global": True} 
    ]}
    query_filter ={"$and": [access_filter]}
    # print(current_user)
    if keyword:
        keyword_regex = normalize_fuzzy_regex_safe(keyword)
        query_filter["$and"] .append({
            "$or":[
            {"name": {"$regex": keyword_regex, "$options": "i"}},
            {"title": {"$regex": keyword_regex, "$options": "i"}},
            {"industry": {"$regex": keyword_regex, "$options": "i"}},
            {"location": {"$regex": keyword_regex, "$options": "i"}},
            {"domain_url": {"$regex": keyword_regex, "$options": "i"}},
            {"company_name": {"$regex": keyword_regex, "$options": "i"}},
            {"email_id": {"$regex": keyword_regex, "$options": "i"}},
            {"primary_number": {"$regex": keyword_regex, "$options": "i"}},
        ]
}) 
    # Individual field filters
    filters = []
    if name:
        name = normalize_fuzzy_regex_safe(name)
        filters.append({"name": {"$regex": name, "$options": "i"}})
    if title:
        title = normalize_fuzzy_regex_safe(title)
        filters.append({"title": {"$regex": title, "$options": "i"}})
    if company:
        company = normalize_fuzzy_regex_safe(company)
        filters.append({"company_name":{"$regex":company,"$options":"i"}})
    if location:
        location = normalize_fuzzy_regex_safe(location)
        filters.append({"location": {"$regex": location, "$options": "i"}})
    if industry:
        industry = normalize_fuzzy_regex_safe(industry)
        filters.append({"industry": {"$regex": industry, "$options": "i"}})

    if filters:
        query_filter["$and"].extend(filters)
        # if "$or" in query_filter:
        #     query_filter = {"$and": [query_filter] + filters}
        # else:
        #     query_filter = {"$and": filters}
    sort_by = (params.sort_by or "name").lower()
    sort_order = (params.sort_order or "asc").lower()
    if sort_by not in ALLOWED_SORT_FIELDS:
        sort_by = "name"
    sort_direction = DESCENDING if sort_order == "desc" else ASCENDING

    pipeline = [{"$match": query_filter}]
    if sort_by == "location":
        pipeline.append({
            "$addFields": {
                "_sort_city": {"$ifNull": ["$city", "\uffff"]},
                "_sort_country": {"$ifNull": ["$country", "\uffff"]}
            }
        })
        pipeline.append({"$sort": {"_sort_city": sort_direction, "_sort_country": sort_direction}})
    else:
        field_name = SORT_FIELD_MAP[sort_by]
        # pipeline.append({"$addFields": {f"_sort_field": {"$ifNull": [f"${field_name}", "\uffff"]}}})
        pipeline.append({"$addFields": {
        "_sort_field": {
            "$cond": {
                "if": {
                    "$or": [
                        {"$eq": [f"${field_name}", None]},
                        {"$eq": [f"${field_name}", ""]},
                        {
                            "$regexMatch": {
                                "input": {"$toString": f"${field_name}"},
                                "regex": r"^-+$"
                            } }
                        ]},
                        
                "then": "\uffff",  
                "else": {"$toLower": f"${field_name}"}}}}})
        pipeline.append({"$sort": {"_sort_field": sort_direction}})

    skip = (params.page - 1) * params.size
    pipeline.append({"$skip": skip})
    pipeline.append({"$limit": params.size})
     
    docs = await database.leads.aggregate(pipeline).to_list(length=params.size)
    total_count = await database.leads.count_documents(query_filter)
    total_pages = (total_count + params.size - 1) // params.size


    page_result = Page.create(
        items=docs,
        total=total_count,
        params=params,
        total_pages=total_pages
    )

    return page_result


@leads_router.get("/unique")
async def get_all_unique_values():

    pipeline = [
        {
            "$facet": {
                "titles": [
                    {"$match": {"title": {"$nin": [None, "", "-"]}}},
                    {
                        "$group": {
                            "_id": {"$toLower": "$title"},
                            "value": {"$first": "$title"}
                        }
                    },
                    {"$sort": {"value": 1}},
                    {"$project": {"_id": 0, "value": 1}}
                ],
                "industries": [
                    {"$match": {"industry": {"$nin": [None, "", "-"]}}},
                    {
                        "$group": {
                            "_id": {"$toLower": "$industry"},
                            "value": {"$first": "$industry"}
                        }
                    },
                    {"$sort": {"value": 1}},
                    {"$project": {"_id": 0, "value": 1}}
                ],
                "companies": [
                    {"$match": {"company_name": {"$nin": [None, "", "-"]}}},
                    {
                        "$group": {
                            "_id": {"$toLower": "$company_name"},
                            "value": {"$first": "$company_name"}
                        }
                    },
                    {"$sort": {"value": 1}},
                    {"$project": {"_id": 0, "value": 1}}
                ],
                "location":[
                     {"$match": {"location": {"$nin": [None, "", "-"]}}},
                    {
                        "$group": {
                            "_id": {"$toLower": "$location"},
                            "value": {"$first": "$location"}
                        }
                    },
                    {"$sort": {"value": 1}},
                    {"$project": {"_id": 0, "value": 1}}

                ]
            }
        }
    ]

    result = await database.leads.aggregate(pipeline).to_list(length=1)
    data = result[0]
   
    formatted_response = {
        "titles": [item["value"] for item in data["titles"]],
       
        "industries": [item["value"] for item in data["industries"]],
        "companies": [item["value"] for item in data["companies"]],
        "location":[item["value"] for item in data["location"]]
    }

    return formatted_response


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
        "owner_id": str(current_user["id"])
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
        "owner_id": str(current_user["id"])
    })

    if not existing_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    update_fields = {
        k: v for k, v in lead_update.dict().items()
        if v is not None
    }

    if not update_fields:
        raise HTTPException(status_code=400, detail="No valid field to update")


    if "company_id" in update_fields or "company_name" in update_fields:

        company_id = await resolve_company(
            database=database,
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
                {"_id": object_id,"owner_id": str(current_user["id"])},
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
