from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi.responses import StreamingResponse
from io import BytesIO
import pandas as pd

import json
from database import get_database 
from Auth.create_access import get_current_user 

export_router = APIRouter(prefix="/export",tags=['export'])

@export_router.get("/export/leads/excel")
async def export_leads_excel(db: AsyncIOMotorDatabase = Depends(get_database),current_user=Depends(get_current_user)):
    leads_cursor = db["leads"].find()
    leads = await leads_cursor.to_list(length=None)


    headers = set()
    if leads:
        for lead in leads:
            headers.update(lead.keys())
    headers = list(headers)

    data = []
    for lead in leads:
        row = {}
        for h in headers:
            if h == "_id":
                row["id"] = str(lead["_id"])
            else:
                value = lead.get(h, "")
                if isinstance(value, (list, dict)):
                    value = json.dumps(value)
                row[h] = value
        data.append(row)

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leads")
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=leads.xlsx"}
    )



@export_router.get("/export/company/excel")
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
