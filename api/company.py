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

from fastapi_pagination import Page,add_pagination
from fastapi_pagination.ext.motor import paginate

from schemas.company_schema import CompanyBase,CompanyCreate,CompanyResponse,CompanyUpdate,CompanyStatus
from auth.create_access import get_current_user
from services.create_or_import import create_single_company,import_company_from_file
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


@company_router.get("/read_company",response_model=Page[CompanyResponse])
async def get_all_company(
    params:CustomParams=Depends(),
    keyword: str = None,
    employee_count:str=None,
    revenue:str=None,
    country:str=None,
    vertical:str=None,
    location:str=None,
    current_user=Depends(get_current_user)
):
    
    query = {}

    if keyword and keyword.strip():
        keyword = keyword.strip()
        keyword=normalize_fuzzy_regex_safe(keyword)

        query["$or"] = [
            {"company_name": {"$regex": keyword, "$options": "i"}},
            # {"country": {"$regex": keyword, "$options": "i"}},
            # {"gross_revenue":{"regex":keyword,"$options":"i"}},
            {"industry": {"$regex": keyword, "$options": "i"}},
            {"domain_url":{"$regex":keyword,"$options":"i"}},
            # {"employee_size":{"regex":keyword,"$options":"i"}},
            # {"founding_year":{"regex":keyword,"$options":"i"}},
            # {"company_linkedin_source":{"regex":keyword,"$options":"i"}}
        ]
    
    filter=[]
    
    if vertical and vertical.strip():
           industry=normalize_fuzzy_regex_safe(vertical)
           filter.append({
        "industry": {"$regex": industry, "$options": "i"}})

   

    if location and location.strip():
        country_regex=normalize_fuzzy_regex(location)
        filter.append(
        {"country": {"$regex": country_regex, "$options": "i"}}) 
        
    # if location and location.strip():
    #     filter.append(
    #         {"city":{"$regex":location,"$options":"i"}},
    #         {"state":{"$regex":location,"$options":"i"}})
    if employee_count and employee_count.strip():
        #   employee_size=normalize_fuzzy_regex(employee_count)
          filter.append(
            {"employee_size":{"$regex":employee_count.strip(),"$options":"i"}})    
    if revenue and revenue.strip():
        revenue=normalize_fuzzy_regex(revenue)
        filter.append(
        {"gross_revenue": {"$regex": revenue.strip(), "$options": "i"}}
    ) 
    if filter:
        query = {"$and": filter}

    async def transform(items):
        for doc in items:
             company_id = doc["_id"]

             leads = await database.leads.find(
            {"company_id": company_id},
            {
                "name": 1,
                "primary_number": 1,
                "title": 1,
                "personal_linkedin_source": 1,
                # "email_id":1
            }
        ).to_list(None)
             for lead in leads:
                  lead["id"] = str(lead.pop("_id"))
 
             doc["leads"] = leads
             doc["id"] = str(doc.pop("_id"))
        return items

    return await paginate(
        database.company,
        query,
        transformer=transform,
        params=params
    )


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
        "owner_id": str(current_user["_id"])
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
        "owner_id": str(current_user["_id"])
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
        "owner_id": str(current_user["_id"])})
    
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
   