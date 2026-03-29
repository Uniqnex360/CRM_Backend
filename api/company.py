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
from bson import ObjectId
from fastapi_pagination import Page,add_pagination
from fastapi_pagination.ext.motor import paginate,create_page

from schemas.company_schema import CompanyBase,CompanyCreate,CompanyResponse,CompanyUpdate,CompanyStatus
from auth.create_access import get_current_user
from services.create_or_import import create_single_company,import_company_from_file
from services.company_read import build_company_filters
from utils.custom_pagination import CustomParams
from utils.clean_data import normalize_fuzzy_regex,normalize_fuzzy_regex_safe
company_router=APIRouter(prefix="/company",tags=['companies'])

@company_router.post("/create_company")
async def create_company(
    company: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user=Depends(get_current_user)
):

    if file:
        return await import_company_from_file(
            file,
            current_user,
            database
        )

    if company:
        try:
            company_data = json.loads(company)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON format")

        return await create_single_company(
            company_data,
            current_user,
            database
        )
    raise HTTPException(
        status_code=400,
        detail="Provide either company JSON or file upload"
    )

@company_router.get("/read_company", response_model=Page[CompanyResponse])
async def get_all_company(
    params: CustomParams = Depends(),
    keyword: str = None,
    employee_count: str = None,
    revenue: str = None,
    country: str = None,
    vertical: str = None,
    location: str = None,
    current_user=Depends(get_current_user)
):
    skip = (params.page - 1) * params.size
    limit = params.size


    filters = build_company_filters(keyword, vertical, location, employee_count, revenue)

   
    if current_user["role"] == "super_admin":
        final_match = {}
    else:
        tenant_id = ObjectId(current_user["tenant_id"])  

        tenant_filter = {
            "$or": [
                {"tenant_id": tenant_id},
                {"is_global": True}
            ]
        }

        if filters:
            final_match = {"$and": filters["$and"] + [tenant_filter]}
        else:
            final_match = tenant_filter

    # 🔹 Step 3: Get total count (FAST)
    total = await database.company.count_documents(final_match)
    print("Total with filter:",total)

    # 🔹 Step 4: Aggregation pipeline (OPTIMIZED)
    pipeline = [
        {"$match": final_match},
        {"$sort": {"company_name": 1}},

        # ✅ PAGINATE FIRST (BIG PERFORMANCE FIX)
        {"$skip": skip},
        {"$limit": limit},

        # ✅ LOOKUP ONLY PAGINATED RECORDS
        {
            "$lookup": {
                "from": "leads",
                "let": {"companyId": "$_id"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$eq": ["$company_id", {"$toString": "$$companyId"}]
                            },
                            **({} if current_user["role"] == "super_admin" else {
                                "$or": [
                                    {"tenant_id": tenant_id},
                                    {"is_global": True}
                                ]
                            })
                        }
                    },
                    {"$limit": 5}
                ],
                "as": "leads"
            }
        }
    ]

    cursor = database.company.aggregate(pipeline)
    items = await cursor.to_list(length=limit)

    
    for company in items:
        company["_id"] = str(company["_id"])

        if "tenant_id" in company and isinstance(company["tenant_id"], ObjectId):
            company["tenant_id"] = str(company["tenant_id"])

        if "owner_id" in company and isinstance(company["owner_id"], ObjectId):
            company["owner_id"] = str(company["owner_id"])

        if "leads" in company:
            for lead in company["leads"]:
                if "_id" in lead and isinstance(lead["_id"], ObjectId):
                    lead["id"] = str(lead["_id"])
                    del lead["_id"]

    return create_page(items, total, params)

# @company_router.get("/read_company", response_model=Page[CompanyResponse])
# async def get_all_company(
#     params: CustomParams = Depends(),
#     keyword: str = None,
#     employee_count: str = None,
#     revenue: str = None,
#     country: str = None,
#     vertical: str = None,
#     location: str = None,
#     current_user=Depends(get_current_user)
# ):
#     skip = (params.page - 1) * params.size
#     limit = params.size


#     filters = build_company_filters(keyword, vertical, location, employee_count, revenue)

#     if current_user["role"] == "super_admin":
#         final_match = filters if filters else {}
#     else:
        
#         tenant_id = str(current_user.get("tenant_id"))
#         tenant_filter = {"$or": [{"tenant_id": ObjectId(tenant_id)}, {"is_global": True}]}
#         if filters and "$and" in filters:
#             final_match = {"$and": filters["$and"] + [tenant_filter]}
#         else:
#             final_match = tenant_filter

#     # Aggregation pipeline
#     pipeline = [
#         {"$match": final_match},
#         {"$sort": {"company_name": 1}},
#         {
#             "$lookup": {
#                 "from": "leads",
#                 "let": {"companyId": "$_id"},
#                 "pipeline": [
#                     {"$match": {
#                         "$expr": {"$eq": ["$company_id", {"$toString": "$$companyId"}]},
#                         **({} if current_user["role"] == "super_admin" else {"$or": [{"tenant_id": ObjectId(tenant_id)}, {"is_global": True}]})
#                     }},
#                     {"$limit": 5}
#                 ],
#                 "as": "leads"
#             }
#         },
#         {"$facet": {
#             "metadata": [{"$count": "total"}],
#             "data": [{"$skip": skip}, {"$limit": limit}]
#         }}
#     ]

#     cursor = database.company.aggregate(pipeline)
#     agg_result = await cursor.to_list(1)

#     if agg_result:
#         total = agg_result[0]["metadata"][0]["total"] if agg_result[0]["metadata"] else 0
#         items = agg_result[0]["data"]
#     else:
#         total = 0
#         items = []

   
#     for company in items:
#         company["_id"] = str(company["_id"])
#         if "tenant_id" in company and isinstance(company["tenant_id"], ObjectId):
#             company["tenant_id"] = str(company["tenant_id"])
#         if "owner_id" in company and isinstance(company["owner_id"], ObjectId):
#             company["owner_id"] = str(company["owner_id"])
#         if "leads" in company:
#             for lead in company["leads"]:
#                 if "_id" in lead and isinstance(lead["_id"], ObjectId):
#                     lead["id"] = str(lead["_id"])
#                     del lead["_id"]

#     return create_page(items, total, params)

@company_router.get("/read_company/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,
    current_user=Depends(get_current_user)
):
    try:
        object_id = ObjectId(company_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid company ID format")

    company = await database.company.find_one({
        "_id": object_id,
        "owner_id": str(current_user["id"])
    })

    if not company:
        raise HTTPException(status_code=404, detail="company not found")

    company["id"] = str(company["_id"])
    del company["_id"]

    return company


@company_router.put("/update_company/{company_id}",response_model=CompanyResponse)
async def update_company(company_id:str,lead_update:CompanyUpdate,current_user=Depends(get_current_user)):
    try:
        object_id=ObjectId(company_id)
    except:
        raise HTTPException(status_code=400,detail="Invalid company ID format")
    
    existing_company = await database.company.find_one({
        "_id": object_id,
        "owner_id": str(current_user["id"])
        })
    if not existing_company:
        raise HTTPException(status_code=404, detail="company not found")
    
    
    update_data = {k: v for k, v in lead_update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400,detail="No valid field")
    update_data["updated_at"]=datetime.utcnow()
  
    await database.company.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )

    company= await database.company.find_one({"_id": object_id})
    company["id"] = str(company.pop("_id"))
    return company




@company_router.patch("/company_status/{company_id}",response_model=CompanyResponse)
async def company_status(company_id:str,
                       status_update:CompanyStatus,
                       current_user=Depends(get_current_user)):
      try:
        object_id=ObjectId(company_id)
      except:
          raise HTTPException(status_code=400,detail="Invalid company ID format")
       
      company = await database.company.find_one({
        "_id": object_id,
        "owner_id": str(current_user["id"])})
    
    #   if not company:
    #     raise HTTPException(status_code=404, detail="company not found")
    
      update_fields = {k: v for k, v in status_update.dict().items() if v is not None}


      updated_company=await database.company.find_one_and_update(
                {"_id": object_id},
            {"$set": update_fields},
         return_document=ReturnDocument.AFTER
           )

      if not updated_company:
           raise HTTPException(status_code=404, detail="Company not found")

      updated_company["id"] = str(updated_company["_id"])
      del updated_company["_id"]

      return updated_company
   