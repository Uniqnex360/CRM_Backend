from fastapi import APIRouter, Depends,Body
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi.responses import StreamingResponse
from io import BytesIO
from typing import List
from bson import ObjectId
import pandas as pd

import json
from database import get_database 
from auth.create_access import get_current_user 

export_router = APIRouter(prefix="/export",tags=['export'])

export_columns = [
    "month","date",
    "industry","company_name",
    "domain_url","company_linkedin_source",
    "name","title",
    "personal_linkedin_source",
    "email_id","primary_number",
    "hq_no","address",
    "city","state",
    "country","founding_year",
    "gross_revenue","revenue","employee_size","amazon_existing","vertical","sub_category","product_count", "cms"]

@export_router.post("/leads/excel")
async def export_leads_excel(
    payload: dict = Body(default={}),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user)
):
    lead_ids = payload.get("lead_ids", [])
    object_ids = [ObjectId(str(id)) for id in lead_ids if id]
    if object_ids: 
        leads = await db["leads"].find({"_id": {"$in": object_ids}}).to_list(length=None)
    else:
       leads = await db["leads"].find().to_list(length=None) 
    company_ids = list(
        set([lead.get("company_id") for lead in leads if lead.get("company_id")])
    )
    companies_map = {}

    if company_ids:
        companies_cursor = db["company"].find(
            {"_id": {"$in": company_ids}},
            {"company_name": 1}
        )
        companies = await companies_cursor.to_list(length=None)

        companies_map = {
            str(c["_id"]): c.get("company_name")
            for c in companies
        }
    export_rows = []

    for lead in leads:

        row = {}

        for col in export_columns:
  
          
            if col == "company_name":
                row[col] = companies_map.get(
                    str(lead.get("company_id")),
                    lead.get("company_name", "")
                )
                continue

            
            # if col == "domain_url":
            #     row[col] = (
            #         lead.get("url")
            #         or lead.get("domain")
            #         or ""
            #     )
            #     continue
            # if col=="gross_revenue":
            #     row[col]=(
            #         lead.get("revenue") 
            #         or lead.get("gross_revenue")
            #         or ""
            #     )
            
            # if col=="employee_size":
            #      row[col]=(
            #          lead.get("employee_size")
            #          or lead.get("headcount")
            #          or ""
            #      )
            # if col=="title":
            #      row[col]=(
            #          lead.get("title")
            #          or lead.get("role")
            #          or ""
            #      )

            value = lead.get(col, "")

          
            if isinstance(value, (list, dict)):
                value = json.dumps(value)

            row[col] = value if value is not None else ""

        export_rows.append(row)

    
    df = pd.DataFrame(export_rows)

   
    df = df.reindex(columns=export_columns, fill_value="")

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leads")

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=leads.xlsx"
        }
    )


@export_router.get("/company/excel")
async def export_company_excel(db: AsyncIOMotorDatabase = Depends(get_database),current_user=Depends(get_current_user)):
    company_cursor = db["company"].find()
    company = await company_cursor.to_list(length=None)


    headers = set()
    if company:
        for x in company:
            headers.update(x.keys())
    headers = list(headers)

    data = []
    for x in company:
        row = {}
        for h in headers:
            if h == "_id":
                row["id"] = str(x["_id"])
            else:
                value = x.get(h, "")
                if isinstance(value, (list, dict)):
                    value = json.dumps(value)
                row[h] = value
        data.append(row)

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="company")
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=company.xlsx"}
    )
