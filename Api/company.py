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

from schemas.company_schema import CompanyBase,CompanyCreate,CompanyResponse,CompanyUpdate
from Auth.create_access import get_current_user
from services.create_or_import import create_single_company,import_company_from_file

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


@company_router.get("/read_company")
async def get_all_company(
    keyword: str = None,
    vertical: str = None,
    employees_count:str=None,
    revenue:str=None,

    current_user=Depends(get_current_user)
):
    query = {"owner_id": str(current_user["_id"])}

    if keyword:
        query["keyword"] = {"$in": [keyword]}

    if vertical:
        query["domain"] = vertical

    if employees_count:
        query["employees_count"]= employees_count
    
    if revenue:
        query["revenue"]=revenue

    companies = []
    async for company in database.company.find(query):
        company["id"] = str(company["_id"])
        del company['_id']
        companies.append(company)

    return companies


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
        "owner_id": str(current_user["_id"])})
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
    company["id"] = str(company["_id"])
    return company


class CompanyStatus(BaseModel):
    is_active:Optional[bool]=None
    added_to_favourites:Optional[bool]=None

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
    
      if not company:
        raise HTTPException(status_code=404, detail="company not found")
    
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
   