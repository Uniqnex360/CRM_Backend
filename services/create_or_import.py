from datetime import datetime
from fastapi import HTTPException, UploadFile
from io import BytesIO
import pandas as pd
from typing import Dict, List
from schemas.lead_schema import LeadCreate
from schemas.company_schema import CompanyCreate
from utils.company_resolve import resolve_company
from bson import ObjectId
from utils.clean_data import clean_phone,clean_string,extract_primary_email

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

    for key, value in new_lead.items():
     if isinstance(value, ObjectId):
        new_lead[key] = str(value)

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

    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df = df.where(pd.notnull(df), None)

    leads_to_insert: List[Dict] = []
    failed_rows = []

    for index, row in df.iterrows():
        row_data = row.to_dict()

        for key, value in row_data.items():
           if pd.isna(value):
             row_data[key] = None
        try:
            
            if row_data.get("ecommerce") is None:
                row_data["ecommerce"] = ""

            personal_linkedin = (row_data.get("personal_linkedin_source") or row_data.get("source_link"))
            row_data["personal_linkedin_source"] = personal_linkedin
            
            domain =row_data.get("domain")
            url = row_data.get("url")
            row_data["domain_url"] = url or domain

            country = row_data.get("country")
            geo = row_data.get("geo")
            row_data["country"] = country or geo
           
            if row_data.get("company_name"):
               row_data["company_name"] = row_data["company_name"].strip()
            
            row_data["email_id"] = extract_primary_email(row_data.get("email_id"))

            row_data["hq_no"] = clean_phone(
                row_data.get("hq_no")
            )
            
            row_data["name"] = clean_string(
                row_data.get("name")
            )
         
            if row_data.get("date") is not None:
                 row_data["date"] = str(row_data["date"])
 

            if row_data.get("founding_year") is not None:
                row_data["founding_year"] = str(row_data["founding_year"])
            if row_data.get("headcount") is not None:
                row_data["headcount"] = str(row_data["headcount"])

            lead_obj = LeadCreate(**row_data)

            if lead_obj.email_id:
                existing = await database.leads.find_one({
                                "email_id": lead_obj.email_id
                             })
                if existing:
                     raise ValueError("Lead with this email already exists")


            elif lead_obj.direct_no:
                   existing = await database.leads.find_one({
                             "direct_no": lead_obj.direct_no
                                    })
                   if existing:
                         raise ValueError("Lead with this direct_no already exists")
          


            lead_dict = lead_obj.dict()
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
                
                for lead in leads_to_insert:  
                    company_name = lead.get("company_name")
                    if company_name:
                 
                        company_data = {
                            "company_name": lead.get("company_name"),
                            "company_linkedin_source":lead.get("company_linkedin_source"),
                            "geo": lead.get("geo"),
                            "country": lead.get("country"),
                            "revenue": lead.get("revenue"),
                            "gross_revenue": lead.get("gross_revenue"),
                            "amazon_existing":lead.get("amazon_existing"),
                            "industry": lead.get("industry"),
                            "vertical": lead.get("vertical"),
                            "founding_year": lead.get("founding_year"),
                            "domain": lead.get("domain"),
                            "url": lead.get("url"),
                            "employee_size": lead.get("employee_size"),
                            "headcount": lead.get("headcount")
                        }
                        company_data = {k: v for k, v in company_data.items() if v is not None}
                        company_id=await resolve_company(
                                 database=database,
                             company_data=company_data)

                    # company_id = await resolve_company(
                    #       database=database,
                    #       company_name=lead.get("company_name") )

                        lead["company_id"] = company_id
                    lead.pop("company_name", None)

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