from datetime import datetime
from fastapi import HTTPException, UploadFile
from io import BytesIO
import pandas as pd
from typing import Dict, List
from schemas.lead_schema import LeadCreate
from schemas.company_schema import CompanyCreate
from utils.company_resolve import resolve_company
from bson import ObjectId
from utils.clean_data import clean_phone,clean_string,extract_primary_email,clean_company_name,clean_roles,clean_location_fields,clean_part

async def create_single_lead(
    lead_data: Dict,
    current_user,
    database
):  
    
    
    city = clean_part(lead_data.get("city"))
    country = clean_part(lead_data.get("country"))
    lead_data["city"] = city
    lead_data["country"] = country
    lead_data["location"] = ", ".join([v for v in [city, country] if v]) or None

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
    

    if not lead_obj.email_id and not lead_obj.primary_number:
        raise HTTPException(
            status_code=400,
            detail="Either email_id or primary_number is required"
        )
    company_id = await resolve_company(
    database=database,
    company_data={"company_name": lead_obj.company_name})
       
    industry = lead_data.get("industry")
    vertical = lead_data.get("vertical")
    
    industry_name = clean_string(industry or vertical)
    industry_id = None
    
    if industry_name:
        existing_industry = await database.industry.find_one({
            "name": {"$regex": f"^{industry_name}$", "$options": "i"}
        })
    
        if not existing_industry:
            result = await database.industry.insert_one({
                "name": industry_name,
                "created_at": datetime.utcnow()
            })
            industry_id = result.inserted_id
        else:
            industry_id = existing_industry["_id"]
    
  
    lead_dict = lead_obj.dict()
    lead_dict["owner_id"] = str(current_user["id"])
    lead_dict["location"] = lead_data.get("location")
    lead_dict["company_id"]=company_id
    lead_dict["created_by"] = ObjectId(current_user["id"])  
    lead_dict["created_at"] = datetime.utcnow()
    if current_user["role"] == "super_admin":
         lead_dict["is_global"] = True
    else:
          lead_dict["is_global"] = False
    lead_dict["added_to_favourites"] = False
    lead_dict["is_active"] = True
    lead_dict["tenant_id"] = ObjectId(current_user["tenant_id"])
    lead_dict["company_id"] = company_id
    
    lead_dict["industry"] = industry_name
    lead_dict["industry_id"] = industry_id
    # lead_dict["company_name"] = lead_obj.company_name

    company_users = await database.user.find({"company_ids": company_id}).to_list(None)
    shared_user_ids = [str(u["_id"]) for u in company_users if u["_id"] != current_user["_id"]]
    lead_dict["shared_with_users"] = shared_user_ids

    result = await database.leads.insert_one(lead_dict)

    new_lead = await database.leads.find_one({"_id": result.inserted_id})

    new_lead["id"] = str(new_lead["_id"])
    del new_lead["_id"]

    for key, value in new_lead.items():
     if isinstance(value, ObjectId):
        new_lead[key] = str(value)

    return new_lead


##---------LEADS Import from file-------------##
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
    # print("Columns:", df.columns.tolist())
    df = df.where(pd.notnull(df), None)
    emails = [e for e in df.get("email_id", []) if e]
    phones = [p for p in df.get("primary_number", []) if p]
    
    existing_leads = await database.leads.find(
        {
            "$or": [
                {"email_id": {"$in": emails}},
                {"primary_number": {"$in": phones}}
            ]
        },
        {"email_id": 1, "primary_number": 1}
    ).to_list(None)
    
    existing_emails = {e.get("email_id") for e in existing_leads if e.get("email_id")}
    existing_phones = {e.get("primary_number") for e in existing_leads if e.get("primary_number")}
    company_names = list(set(
        clean_company_name(str(c).strip())
        for c in df.get("company_name", []) if c
    ))
    
    existing_companies = await database.company.find(
        {"company_name": {"$in": company_names}}
    ).to_list(None)
    
    company_map = {c["company_name"]: c["_id"] for c in existing_companies}
    new_companies = []

    for name in company_names:
        if name not in company_map:
                new_companies.append({
            "company_name": name,
            "owner_id": str(current_user["id"]),
            "created_at": datetime.utcnow()
        })

    if new_companies:
        result = await database.company.insert_many(new_companies)

        for name, _id in zip(
        [c["company_name"] for c in new_companies],
        result.inserted_ids
    ):
          company_map[name] = _id
    leads_to_insert: List[Dict] = []
    failed_rows = []
    for index, row in enumerate(df.itertuples(index=False)):
        row_data = row._asdict()
        for key, value in row_data.items():
           if pd.isna(value):
             row_data[key] = None
        try:
            
            if row_data.get("ecommerce") is None:
                row_data["ecommerce"] = ""
            
        
            primary_number =row_data.get("primary_number")
            hq_no = row_data.get("hq_no")
            row_data["primary_number"] = primary_number or hq_no

            personal_linkedin_source=row_data.get("personal_linkedin_source") 
            source_link=row_data.get("source_link")
            row_data["personal_linkedin_source"] = personal_linkedin_source or source_link
            
            domain =row_data.get("domain")
            url = row_data.get("url")
            row_data["domain_url"] = url or domain

            title=row_data.get("title")
            role=row_data.get("role")
            title=title or role
            title=clean_roles(title)
            row_data["title"]=title

            city = row_data.get("city")
            state = row_data.get("state")
            country = row_data.get("country")
            
           
            if city and "," in str(city):
                parts = [p.strip() for p in str(city).split(",")]
                city = parts[0] if len(parts) > 0 else None
                state = parts[1] if len(parts) > 1 else state
            

            city, state, country, location = clean_location_fields(city, state, country)
            
            row_data["city"] = city
            row_data["state"] = state
            row_data["country"] = country
            row_data["location"] = location
           
            employee_size=row_data.get("employee_size")
            headcount=row_data.get("headcount")
            row_data["employee_size"]=employee_size or headcount
 
            country = row_data.get("country")
            geo = row_data.get("geo")
            row_data["country"] = country or geo
         
            industry=row_data.get("industry")
            vertical=row_data.get("vertical")
            row_data["industry"]=industry or vertical
            industry_id = None

            if industry_name:
                industry_name = clean_string(industry_name)
            
                existing_industry = await database.industry.find_one({
                    "name": {"$regex": f"^{industry_name}$", "$options": "i"}
                })
            
                if not existing_industry:
                    result = await database.industry.insert_one({
                        "name": industry_name,
                        "created_at": datetime.utcnow()
                    })
                    industry_id = result.inserted_id
                else:
                    industry_id = existing_industry["_id"]
            
            row_data["industry"] = industry_name      
            row_data["industry_id"] = industry_id
            gross_revenue=row_data.get("gross_revenue")
            revenue=row_data.get("revenue")
            row_data["gross_revenue"]=gross_revenue or revenue
            if row_data.get("company_name"):
               row_data["company_name"] = clean_company_name(row_data["company_name"].strip())
            
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

            if row_data.get("employee_size") is not None:
                row_data["employee_size"] = str(row_data["employee_size"])
            

            if row_data.get("primary_number") is not None:
                row_data["primary_number"] = str(row_data["primary_number"])
                
            keywords = row_data.get("keywords")
            if keywords and isinstance(keywords, str):
                 row_data["keywords"] = [k.strip() for k in keywords.split(",") if k.strip()]

            # print("Before schema company_name:", row_data.get("company_name"))
            lead_obj = LeadCreate(**row_data)
            if lead_obj.email_id and lead_obj.email_id in existing_emails:
                 raise ValueError("Lead with this email already exists")

            # if lead_obj.primary_number and lead_obj.primary_number in existing_phones:
            #      raise ValueError("Lead with this direct_no already exists")


            lead_dict = lead_obj.dict()

            company_name = lead_dict.get("company_name")
            if company_name:
                lead_dict["company_id"] = company_map.get(company_name)
            # print("Lead dict company_name:", lead_dict.get("company_name"))
           
            lead_dict["owner_id"] = str(current_user["id"])
            if current_user.get("role") == "super_admin":
                  lead_dict["is_global"] = True
                  lead_dict["tenant_id"] = None 
            else:
                  lead_dict["is_global"] = False
                  lead_dict["tenant_id"] =ObjectId(current_user["tenant_id"])
            lead_dict["created_by"] = ObjectId(current_user["id"])  
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
                    # print("Lead before company resolve:", lead.get("company_name"))
                    if company_name:
                 
                        company_data = {
                            "company_name":clean_company_name(lead.get("company_name")) ,
                            "company_linkedin_source":lead.get("company_linkedin_source"),
                            "country": lead.get("country"),
                            "city":lead.get("city"),
                            "state":lead.get("state"),
                            "revenue": lead.get("revenue"),
                            "gross_revenue": lead.get("gross_revenue"),
                            "amazon_existing":lead.get("amazon_existing"),
                            "industry": lead.get("industry"),
                            "founding_year": lead.get("founding_year"),
                            "domain_url": lead.get("domain_url"),
                            "employee_size": lead.get("employee_size"),
                            "location":lead.get("location"),
                            "owner_id": str(current_user["id"]),
                            "keywords":lead.get("keywords"),
                    
                        
                        }
                        if current_user.get("role") == "super_admin":
                            company_data["is_global"] = True
                            company_data["tenant_id"] = None  # optional, can omit
                        else:
                            company_data["is_global"] = False
                            company_data["tenant_id"] = str(current_user["tenant_id"])
                        company_data = {k: v for k, v in company_data.items() if v is not None}
                        # print("Company data being sent:", company_data)
                        company_id=await resolve_company(
                                 database=database,
                             company_data=company_data)

                 

                        lead["company_id"] = company_id
                        lead["company_name"] = company_name 
                    # lead.pop("company_name", None)

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
    company_dict["owner_id"] = str(current_user["id"])
    company_dict["tenant_id"]= ObjectId(current_user["tenant_id"])
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
    industry_name = company_dict.get("industry")
    industry_id = None
    
    if industry_name:
        industry_name = clean_string(industry_name)
    
        existing_industry = await database.industry.find_one({
            "name": {"$regex": f"^{industry_name}$", "$options": "i"}
        })
    
        if not existing_industry:
            result = await database.industry.insert_one({
                "name": industry_name,
                "created_at": datetime.utcnow()
            })
            industry_id = result.inserted_id
        else:
            industry_id = existing_industry["_id"]

    company_dict["industry_id"] = industry_id

    result = await database.company.insert_one(company_dict)

    lead_exists = await database.leads.find_one({
    "company_name": company_dict["company_name"]})

    if not lead_exists:
       lead_doc = {
        "name": None,
        "company_name": company_dict["company_name"],
        "email_id": None,
        "company_id": str(result.inserted_id),
        "city": company_dict.get("city"),
        "state": company_dict.get("state"),
        "country": company_dict.get("country"),
        "industry": company_dict.get("industry"),
        "keywords":company_dict.get("keywords"),
        "created_at": datetime.utcnow(),
        "owner_id": ObjectId(current_user["id"]),
        "is_global": current_user["role"] == "super_admin"
       
    }

       await database.leads.insert_one(lead_doc)

    new_company = await database.company.find_one({"_id": result.inserted_id})

    new_company["id"] = str(new_company["_id"])
    new_company["tenant_id"] = str(new_company.get("tenant_id"))
    new_company["owner_id"] = str(new_company.get("owner_id"))
    del new_company["_id"]
    return new_company

async def import_company_from_file(file: UploadFile, current_user, database):
    contents = await file.read()
    inserted_count =0
    if file.filename.endswith(".csv"):
        df = pd.read_csv(BytesIO(contents))
    elif file.filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(BytesIO(contents))
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    df = df.where(pd.notnull(df), None)

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
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
            if row_data.get("founding_year") is not None:
                row_data["founding_year"] = str(row_data["founding_year"])

            company_obj = CompanyCreate(**row_data)

            if not company_obj.company_name:
                raise ValueError("company name is required")

            company_dict = company_obj.dict()
            company_dict["owner_id"] = ObjectId(current_user["_id"])
            company_dict["tenant_id"]= ObjectId(current_user["tenant_id"])
            company_dict["created_at"] = datetime.utcnow()
            company_dict["added_to_favourites"] = False
            company_dict["is_active"] = True

            industry_name = company_dict.get("industry")
            industry_id = None
            
            if industry_name:
                industry_name = clean_string(industry_name)
            
                existing_industry = await database.industry.find_one({
                    "name": {"$regex": f"^{industry_name}$", "$options": "i"}
                })
            
                if not existing_industry:
                    result = await database.industry.insert_one({
                        "name": industry_name,
                        "created_at": datetime.utcnow()
                    })
                    industry_id = result.inserted_id
                else:
                    industry_id = existing_industry["_id"]
        
            company_dict["industry_id"] = industry_id
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
                
                result = await database.company.insert_one(company_dict)

                inserted_count += 1
                company_id = result.inserted_id
                lead = await database.leads.find_one({"company_name": company_dict["company_name"]})

                if not lead:

                    lead_doc = {
                          "name": None,
                          "company_name": clean_company_name(company_dict["company_name"]),
                          "email_id": None,
                          "company_id": str(company_id),
                          "city": company_dict.get("city"),
                          "state": company_dict.get("state"),
                          "country": company_dict.get("country"),
                          "industry": company_dict.get("industry"),
                          "keywords": company_dict.get("keywords"),
                          "created_at": datetime.utcnow(),
                          "owner_id": str(current_user["_id"]),
                           "is_global": current_user["role"] == "super_admin",
                      }
                  
                    await database.leads.insert_one(lead_doc)
        except Exception as e:
            failed_rows.append({
                "row_number": index + 1,
                "error": str(e)
            })

    # if company_to_insert:
    #     await database.company.insert_many(company_to_insert)

    return {
        "total_rows": len(df),
        "inserted": inserted_count,
        "failed": len(failed_rows),
        "errors": failed_rows
    }