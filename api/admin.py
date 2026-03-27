from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from bson import ObjectId
from database import database
from auth.create_access import get_current_user 


from fastapi import APIRouter, Depends, HTTPException
from database import database
from schemas.user_schema import AdminCompanyBase,AdminCompanyResponse
from auth.create_access import super_admin_required


admin_router = APIRouter(prefix="/admin", tags=["admin"])

def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"]
    }

@admin_router.post("/create-organization", response_model=AdminCompanyResponse)
async def create_organization(
    org: AdminCompanyBase,
    current_user=Depends(super_admin_required)
):
    org_dict = org.dict()
    org_dict["created_by"] = current_user["id"]
    org_dict["created_at"] = datetime.utcnow()

    result = await database.organizations.insert_one(org_dict)

    created_org = await database.organizations.find_one({"_id": result.inserted_id})

    return {
        "id": str(created_org["_id"]),
        "org_name": created_org["org_name"],
        "location": created_org.get("location"),
        "industry": created_org.get("industry"),
        "domain_url": created_org.get("domain_url"),
        "created_by": created_org["created_by"],  
    }


@admin_router.put("/assign-company/{user_id}")
async def assign_company(
    user_id: str,
    tenant_id: str,
    current_user=Depends(super_admin_required)
):
    org = await database.organizations.find_one({"_id": ObjectId(tenant_id)})
    if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
    result = await database.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"tenant_id": ObjectId(tenant_id), "role": "admin"}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = await database.users.find_one({"_id": ObjectId(user_id)})

    return {
        "message": "Company assigned successfully",
        "user": user_helper(updated_user)
    }

@admin_router.get("/organizations", response_model=list[AdminCompanyResponse])
async def list_organizations(current_user=Depends(super_admin_required)):
    orgs = []

    async for org in database.organizations.find():
        orgs.append({
            "id": str(org["_id"]),
            "org_name": org["org_name"],
            "location": org.get("location"),
            "industry": org.get("industry"),
            "domain_url": org.get("domain_url"),
            "created_by": org["created_by"],
            "created_at": org.get("created_at")
        })

    return orgs


@admin_router.get("/org-user-count")
async def org_user_count(current_user=Depends(super_admin_required)):

    pipeline = [
        {
            "$group": {
                "_id": "$tenant_id",
                "total_users": {"$sum": 1}
            }
        }
    ]

    result = []
    async for doc in database.users.aggregate(pipeline):
        result.append({
            "tenant_id": doc["_id"],
            "total_users": doc["total_users"]
        })

    return result

@admin_router.get("/org-admin-count")
async def org_admin_count(current_user=Depends(super_admin_required)):

    pipeline = [
        {
            "$match": {"role": "admin"}
        },
        {
            "$group": {
                "_id": "$tenant_id",
                "total_admins": {"$sum": 1}
            }
        }
    ]

    result = []
    async for doc in database.users.aggregate(pipeline):
        result.append({
            "tenant_id": doc["_id"],
            "total_admins": doc["total_admins"]
        })

    return result
@admin_router.get("/email-count")
async def email_count(current_user=Depends(super_admin_required)):

    pipeline = [
        {
            "$group": {
                "_id": "$user_id",
                "total_emails": {"$sum": 1}
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "_id",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {"$unwind": "$user"}
    ]

    result = []
    async for doc in database.email_jobs.aggregate(pipeline):
        result.append({
            "user_id": str(doc["_id"]),
            "user_name": doc["user"]["name"],
            "tenant_id": str(doc["user"]["tenant_id"]),
            "total_emails": doc["total_emails"]
        })

    return result


@admin_router.get("/org-email-count")
async def org_email_count(current_user=Depends(super_admin_required)):

    pipeline = [
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {"$unwind": "$user"},
        {
            "$group": {
                "_id": "$user.tenant_id",
                "total_emails": {"$sum": 1}
            }
        },
        {
            "$lookup": {
                "from": "organizations",
                "localField": "_id",
                "foreignField": "_id",
                "as": "org"
            }
        },
        {"$unwind": {"path": "$org", "preserveNullAndEmptyArrays": True}}
    ]

    result = []
    async for doc in database.email_jobs.aggregate(pipeline):
        result.append({
            "tenant_id": str(doc["_id"]),
            "org_name": doc["org"]["org_name"] if doc.get("org") else None,
            "total_emails": doc["total_emails"]
        })

    return result