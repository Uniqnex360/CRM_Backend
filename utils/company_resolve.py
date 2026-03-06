
from bson import ObjectId
from fastapi import HTTPException
from datetime import datetime


async def resolve_company(database, company_id=None, company_name=None, company_data=None):

    if company_id:
        object_id = ObjectId(company_id)

        existing = await database.company.find_one({"_id": object_id})

        if not existing:
            raise HTTPException(status_code=404, detail="Company not found")

        return existing["_id"]

    if company_data:

        company_name = company_data.get("company_name")

        if not company_name:
            raise HTTPException(status_code=400, detail="company_name required")

        company_name_norm = company_name.strip().lower()

        existing = await database.company.find_one({
            "company_name": {"$regex": f"^{company_name_norm}$", "$options": "i"}
        })

        if existing:

            update_fields = {}

            for key, value in company_data.items():
                if value and not existing.get(key):
                    update_fields[key] = value

            if update_fields:
                update_fields["updated_at"] = datetime.utcnow()

                await database.company.update_one(
                    {"_id": existing["_id"]},
                    {"$set": update_fields}
                )

            return existing["_id"]

        company_data["company_name"] = company_name_norm
        company_data["created_at"] = datetime.utcnow()
        company_data["is_active"] = True

        result = await database.company.insert_one(company_data)

        return result.inserted_id

    raise HTTPException(
        status_code=400,
        detail="Either company_id or company_data required"
    )