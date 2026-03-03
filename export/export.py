from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi.responses import StreamingResponse
from io import BytesIO
import pandas as pd

import json
from database import get_database 
from auth.create_access import get_current_user 

export_router = APIRouter(prefix="/export",tags=['export'])

export_columns = [
    "city",
    "personal_linkedin_source",
    "employee_size",
    "cms",
    "primary_number",
    "sub_category",
    "source",
    "country",
    "email_id",
    "hq_no",
    "company_linkedin_source",
    "month",
    "address",
    "amazon_existing",
    "gross_revenue",
    "name",
    "date",
    "vertical",
    "state",
    "product_count",
    "company_name",
    "industry",
    "founding_year",
    "title",
    "domain_url"
]

@export_router.get("/leads/excel")
async def export_leads_excel(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user)
):

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

          
            if col == "domain_url":
                row[col] = (
                    lead.get("url")
                    or lead.get("domain")
                    or ""
                )
                continue

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
# @export_router.get("/leads/excel")
# async def export_leads_excel(db: AsyncIOMotorDatabase = Depends(get_database),current_user=Depends(get_current_user)):
#     leads_cursor = db["leads"].find()
#     leads = await leads_cursor.to_list(length=None)
#     company_ids = list(
#         set([lead.get("company_id") for lead in leads if lead.get("company_id")])
#     )
#     companies_map = {}

#     if company_ids:
#         companies_cursor = db["company"].find(
#             {"_id": {"$in": company_ids}},
#             {"company_name": 1}
#         )
#         companies = await companies_cursor.to_list(length=None)

#         companies_map = {
#             str(c["_id"]): c.get("company_name")
#             for c in companies
#         }


#     headers = set()
#     if leads:
#         for lead in leads:
#             headers.update(lead.keys())
#     headers.add("company_name")
#     headers = list(headers)

#     data = []
#     for lead in leads:
#         row = {}
#         for h in headers:
#             if h == "_id":
#                 row["id"] = str(lead["_id"])

#             elif h == "company_name":
#                 company_id = lead.get("company_id")
#                 row["company_name"] = companies_map.get(
#                     str(company_id),
#                     lead.get("company_name", "")
#                 )
#             else:
#                 value = lead.get(h, "")
#                 if isinstance(value, (list, dict)):
#                     value = json.dumps(value)
#                 row[h] = value
#         data.append(row)

#     df = pd.DataFrame(data)
#     output = BytesIO()
#     with pd.ExcelWriter(output, engine="openpyxl") as writer:
#         df.to_excel(writer, index=False, sheet_name="Leads")
#     output.seek(0)

#     return StreamingResponse(
#         output,
#         media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#         headers={"Content-Disposition": "attachment; filename=leads.xlsx"}
#     )
# @export_router.get("/leads/excel")
# async def export_leads_excel(
#     db: AsyncIOMotorDatabase = Depends(get_database),
#     current_user=Depends(get_current_user)
# ):

#     cursor = db["leads"].find({
#         "owner_id": str(current_user["_id"])
#     })

#     leads = await cursor.to_list(length=None)

#     LEAD_EXPORT_FIELDS = [
#         "id", "company_id", "name", "title", "email_id",
#         "hq_no", "direct_no", "vertical", "sub_category",
#         "product_count", "emp_size", "revenue",
#         "address", "city", "state", "country",
#         "cms", "ecommerce", "created_at"
#     ]

#     data = []

#     for lead in leads:
#         row = {}

#         for field in LEAD_EXPORT_FIELDS:

#             if field == "id":
#                 row["id"] = str(lead.get("_id"))

#             else:
#                 value = lead.get(field, "")

#                 if isinstance(value, (list, dict)):
#                     value = json.dumps(value)

#                 row[field] = value

#         data.append(row)

#     df = pd.DataFrame(data)

#     output = BytesIO()
#     with pd.ExcelWriter(output, engine="openpyxl") as writer:
#         df.to_excel(writer, index=False, sheet_name="Leads")

#     output.seek(0)

#     return StreamingResponse(
#         output,
#         media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#         headers={
#             "Content-Disposition": "attachment; filename=leads.xlsx"
#         }
#     )


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
