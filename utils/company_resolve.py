from bson import ObjectId
from fastapi import HTTPException
from datetime import datetime
import re

def normalize_text(text: str):
    if not text:
        return None

    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()
  
async def resolve_company(database, company_id=None, company_name=None):

    if company_id:
        object_id = ObjectId(company_id)

        existing = await database.company.find_one({"_id": object_id})

        if not existing:
            raise HTTPException(status_code=404, detail="Company not found")

        return existing["_id"]

    if company_name:

        normalized_name = normalize_text(company_name)

       
        existing = await database.company.find_one({
            "normalized_company_name": {
                "$regex": normalized_name,
                "$options": "i"
            }
        })
        if existing:
            return existing["_id"]

        result = await database.company.insert_one({
            "company_name": company_name.strip(),   
            "normalized_company_name": normalized_name,
            "created_at": datetime.utcnow(),
            "is_active": True
        })

        return result.inserted_id

    raise HTTPException(
        status_code=400,
        detail="Either company_id or company_name required"
)

