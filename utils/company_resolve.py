from bson import ObjectId
from fastapi import HTTPException
from datetime import datetime

async def resolve_company(database, company_id=None, company_name=None):


    if company_id:
        try:
            object_id = ObjectId(company_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid company_id format")

        existing = await database.company.find_one({"_id": object_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Company not found")

        return str(object_id)

    
    if company_name:

        existing = await database.company.find_one({
            "company_name": company_name
        })

        if existing:
            return str(existing["_id"])

        company_name = company_name.strip().lower()
        result = await database.company.insert_one({
            "company_name": company_name,
            "created_at": datetime.utcnow(),
            "is_active": True
        })
      
        return str(result.inserted_id)

    raise HTTPException(
        status_code=400,
        detail="Either company_id or company_name required"
    )