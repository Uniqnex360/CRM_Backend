from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import List
from fastapi import Query
from bson import ObjectId
from database import database
from fastapi import APIRouter, Depends, HTTPException
from database import database
from schemas.user_schema import AdminCompanyBase,AdminCompanyResponse,AssignCompanyRequest,UserResponse

from auth.create_access import super_admin_required
from pydantic import BaseModel
from typing import List

admin_router = APIRouter(prefix="/admin", tags=["admin"])

def user_helper(user) -> dict:
    return {
       "id": str(user["_id"]),
        "name": user.get("name"),
        "email": user.get("email"),
        "role": user.get("role")
    }

@admin_router.post("/create-organization", response_model=AdminCompanyResponse)
async def create_organization(
    org: AdminCompanyBase,
    current_user=Depends(super_admin_required)
):   
    existing_org = await database.organizations.find_one(
           {"org_name": {"$regex": f"^{org.org_name}$", "$options": "i"}}
           
    )
    
    if existing_org:
        raise HTTPException(
            status_code=400,
            detail="Organization with this name  already exists"
        )
    
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



class PaginatedUsers(BaseModel):
    total: int
    page: int
    size: int
    data: List[UserResponse]  

@admin_router.get("/unassigned", response_model=PaginatedUsers)
async def get_unassigned_users(page: int = 1, size: int = 10, current_user=Depends(super_admin_required)):
    skip = (page - 1) * size

    users_cursor = database.users.find({
         "$and": [
        {
            "$or": [
                {"tenant_id": {"$exists": False}},
                {"tenant_id": None}
            ]
        },
        {
            "role": {"$ne": "Super_Admin"} 
        }
    ]
    }).skip(skip).limit(size)

    users = []
    async for user in users_cursor:
        users.append(user_helper(user))

    total_count = await database.users.count_documents({
        "$and": [
        {
            "$or": [
                {"tenant_id": {"$exists": False}},
                {"tenant_id": None}
            ]
        },
        {
            "role": {"$ne": "Super_Admin"}
        }
    ]
    })

    return {
        "total": total_count,
        "page": page,
        "size": size,
        "data": users
    }

@admin_router.put("/assign-company/{user_id}")
async def assign_company(
    user_id: str,
    body: AssignCompanyRequest,  
    current_user=Depends(super_admin_required)
):
    org = await database.organizations.find_one({"_id": ObjectId(body.tenant_id)})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    result = await database.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"tenant_id": ObjectId(body.tenant_id), "role": "admin"}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = await database.users.find_one({"_id": ObjectId(user_id)})

    return {
        "message": "Company assigned successfully",
        "user": user_helper(updated_user)
    }

@admin_router.get("/organizations", response_model=list[dict])
async def list_organizations(current_user=Depends(super_admin_required)):
    orgs = []

    async for org in database.organizations.find():
        assigned_users = []
        async for user in database.users.find({"tenant_id": org["_id"]}):
            assigned_users.append({
                "id": str(user["_id"]),
                "name": user.get("name"),
                "email": user.get("email"),
                "role": user.get("role", "user")
            })

        orgs.append({
            "id": str(org["_id"]),
            "org_name": org["org_name"],
            "location": org.get("location"),
            "industry": org.get("industry"),
            "domain_url": org.get("domain_url"),
            "created_by": org["created_by"],
            "created_at": org.get("created_at"),
            "users": assigned_users 
        })

    return orgs


@admin_router.get("/dashboard-stats")
async def dashboard_stats(current_user=Depends(super_admin_required)):

    pipeline = [{
    "$facet": {
        "org_user_count": [
            {
                "$group": {
                    "_id": "$tenant_id",
                    "total_users": {"$sum": 1}
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
            {
                "$unwind": {
                    "path": "$org",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "tenant_id": {"$toString": "$_id"},
                    "org_name": "$org.org_name",
                    "total_users": 1
                }
            }
        ],

        "org_admin_count": [
            {
                "$match": {"role": "admin"}
            },
            {
                "$group": {
                    "_id": "$tenant_id",
                    "total_admins": {"$sum": 1}
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
            {
                "$unwind": {   
                    "path": "$org",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "tenant_id": {"$toString": "$_id"},
                    "org_name": "$org.org_name",  
                    "total_admins": 1
                }
            }
        ]
    }
}]
    result = []
    async for doc in database.users.aggregate(pipeline):
        result.append(doc)
    email_pipeline = [
    {
        "$addFields": {
            "user_id_obj": {
                "$cond": {
                    "if": {"$eq": [{"$type": "$user_id"}, "string"]},
                    "then": {"$toObjectId": "$user_id"},
                    "else": "$user_id"
                }
            }
        }
    },
    {
        "$facet": {
            "email_count": [
                {
                    "$group": {
                        "_id": "$user_id_obj",
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
                {"$unwind": "$user"},
                {
                    "$project": {
                        "_id": 0,
                        "user_id": {"$toString": "$_id"},
                        "user_name": "$user.name",
                        "tenant_id": {"$toString": "$user.tenant_id"},
                        "total_emails": 1
                    }
                }
            ]
        }
    }
]

    email_result = []
    async for doc in database.email_jobs.aggregate(email_pipeline):
        email_result.append(doc)

    return {
        "user_stats": result[0] if result else {},
        "email_stats": email_result[0] if email_result else {}
    }