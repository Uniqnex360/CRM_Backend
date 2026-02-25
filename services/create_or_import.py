from datetime import datetime
from fastapi import HTTPException, UploadFile
from io import BytesIO
import pandas as pd
from typing import Dict, List
from schemas.lead_schema import LeadCreate
from schemas.company_schema import CompanyCreate
from utils.company_resolve import resolve_company


async def create_single_lead(
    lead_data: Dict,
    current_user,
    database
):

    try:
        lead_obj = LeadCreate(**lead_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    if lead_obj.email_id:
        existing = await database.leads.find_one({
        "email_id": lead_obj.email_id
    })
        
    if existing:
       raise HTTPException(
               status_code=400,
               detail="Lead with this email already exists"
    )
    

    if not lead_obj.email_id and not lead_obj.direct_no:
        raise HTTPException(
            status_code=400,
            detail="Either email_id or direct_no is required"
        )
    
    company_id = await resolve_company(
    database=database,
    company_id=lead_obj.company_id,
    company_name=lead_obj.company_name)

    lead_dict = lead_obj.dict()
    lead_dict["owner_id"] = str(current_user["_id"])
    lead_dict["created_at"] = datetime.utcnow()

    lead_dict["added_to_favourites"] = False
    lead_dict["is_active"] = True

    lead_dict["company_id"] = company_id
    lead_dict.pop("company_name", None)

    result = await database.leads.insert_one(lead_dict)

    new_lead = await database.leads.find_one({"_id": result.inserted_id})

    new_lead["id"] = str(new_lead["_id"])
    del new_lead["_id"]
    return new_lead

async def import_leads_from_file(
    file: UploadFile,
    current_user,
    database
):

    contents = await file.read()

    if file.filename.endswith(".csv"):
        df = pd.read_csv(BytesIO(contents))

    elif file.filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(BytesIO(contents))

    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type"
        )

   
    df = df.where(pd.notnull(df), None)

    leads_to_insert: List[Dict] = []
    failed_rows = []

    for index, row in df.iterrows():
        row_data = row.to_dict()

        for key, value in row_data.items():
           if pd.isna(value):
             row_data[key] = None
 
        if row_data.get("site_search") is None:
               row_data["site_search"] = []

        try:
            
            if row_data.get("ecommerce") is None:
                row_data["ecommerce"] = ""


            if isinstance(row_data.get("site_search"), str):
                row_data["site_search"] = [
                    item.strip()
                    for item in row_data["site_search"].split(",")
                ]
            elif row_data.get("site_search") is None:
                row_data["site_search"] = []

            if row_data.get("company_name"):
               row_data["company_name"] = row_data["company_name"].strip()


            lead_obj = LeadCreate(**row_data)

            if not lead_obj.email_id and not lead_obj.direct_no:
                raise ValueError("Email or direct_no required")

  
            existing = await database.leads.find_one({
                "email_id": lead_obj.email_id
            })

            if existing:
                raise ValueError("Lead with this email already exists")
            
            company_id = await resolve_company(
                  database=database,
                  company_id=lead_obj.company_id,
                  company_name=lead_obj.company_name)


            lead_dict = lead_obj.dict()
            lead_dict["company_id"] = company_id
            lead_dict.pop("company_name", None)
            lead_dict["owner_id"] = str(current_user["_id"])
            lead_dict["created_at"] = datetime.utcnow()
            lead_dict["added_to_favourites"] = False
            lead_dict["is_active"] = True

            leads_to_insert.append(lead_dict)

        except Exception as e:
            failed_rows.append({
                "row_number": index + 1,
                "error": str(e)
            })

  
    if leads_to_insert:
        await database.leads.insert_many(leads_to_insert)

    return {
        "total_rows": len(df),
        "inserted": len(leads_to_insert),
        "failed": len(failed_rows),
        "errors": failed_rows
    }




async def create_single_company(
    company_data: Dict,
    current_user,
    database
):

    try:
        company_obj =CompanyCreate(**company_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    existing = await database.company.find_one({
    "company_name": company_obj.company_name})

    if existing:
       raise HTTPException(
               status_code=400,
               detail="company with this name already exists"
    )
    

    if not company_obj.company_name:
        raise HTTPException(
            status_code=400,
            detail="company_name is required"
        )
    


    company_dict = company_obj.dict()
    company_dict["owner_id"] = str(current_user["_id"])
    company_dict["created_at"] = datetime.utcnow()
    company_dict["added_to_favourites"] = False
    company_dict["is_active"] = True
    company_name_norm = company_obj.company_name.strip().lower()

    existing = await database.company.find_one({
        "company_name": {"$regex": f"^{company_name_norm}$", "$options": "i"}
    })

    if existing:
        await database.company.update_one(
            {"_id": existing["_id"]},
            {"$set": company_dict}
        )
        existing["id"] = str(existing["_id"])
        del existing["_id"]
        return existing

    result = await database.company.insert_one(company_dict)

    new_company = await database.company.find_one({"_id": result.inserted_id})

    new_company["id"] = str(new_company["_id"])
    del new_company["_id"]
    return new_company

async def import_company_from_file(file: UploadFile, current_user, database):
    contents = await file.read()

    if file.filename.endswith(".csv"):
        df = pd.read_csv(BytesIO(contents))
    elif file.filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(BytesIO(contents))
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    df = df.where(pd.notnull(df), None)

    company_to_insert: List[Dict] = []
    failed_rows = []

    for index, row in df.iterrows():
        row_data = row.to_dict()

     
        row_data = {k: (None if pd.isna(v) else v) for k, v in row_data.items()}

        try:
           
            if isinstance(row_data.get("links"), str):
                row_data["links"] = [item.strip() for item in row_data["links"].split(",") if item.strip()]
            if isinstance(row_data.get("keywords"), str):
                row_data["keywords"] = [item.strip() for item in row_data["keywords"].split(",") if item.strip()]
            if row_data.get("founded") is not None:
                row_data["founded"] = str(row_data["founded"])

            company_obj = CompanyCreate(**row_data)

            if not company_obj.company_name:
                raise ValueError("company name is required")

            company_dict = company_obj.dict()
            company_dict["owner_id"] = str(current_user["_id"])
            company_dict["created_at"] = datetime.utcnow()
            company_dict["added_to_favourites"] = False
            company_dict["is_active"] = True

       
            company_name_norm = company_obj.company_name.strip().lower()
            existing = await database.company.find_one({
                "company_name": {"$regex": f"^{company_name_norm}$", "$options": "i"}
            })

            if existing:
        
                await database.company.update_one(
                    {"_id": existing["_id"]},
                    {"$set": company_dict}
                )
            else:
                company_to_insert.append(company_dict)

        except Exception as e:
            failed_rows.append({
                "row_number": index + 1,
                "error": str(e)
            })

    if company_to_insert:
        await database.company.insert_many(company_to_insert)

    return {
        "total_rows": len(df),
        "inserted": len(company_to_insert),
        "failed": len(failed_rows),
        "errors": failed_rows
    }