from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from bson import ObjectId
from database import database
from auth.create_access import get_current_user 


from fastapi import APIRouter, Depends, HTTPException
from database import database

admin_router = APIRouter(prefix="/admin", tags=["admin"])

@admin_router.post("/create_admin", response_model=UserResponse)
async def create_admin(user: UserCreate, current_user=Depends(admin_required)):
    # Check if admin for this tenant already exists
    existing_admin = await database.users.find_one({
        "tenant_id": user.tenant_id,
        "role": "admin"
    })
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin already exists for this organization")
    
    hashed_password = hash_password(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    user_dict["role"] = "admin"
    
    result = await database.users.insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id)
    return user_dict

# from schemas.user_schema import AdminCompanyBase,AdminCompanyResponse
# admin_company_router = APIRouter(prefix="/admin_company", tags=["Admin Companies"])

# @admin_company_router.post("/", response_model=AdminCompanyResponse)

# async def create_admin_company(company: AdminCompanyBase, current_admin=Depends(get_current_user)):
#     doc = {
#         "name": company.name,
#         "created_by": str(current_admin["_id"]),
#         "created_at": datetime.utcnow()
#     }
#     result = await database.admin_companies.insert_one(doc)
#     doc["id"] = str(result.inserted_id)
#     return doc

# @admin_company_router.get("/", response_model=list[AdminCompanyResponse])
# async def get_all_admin_companies(current_admin=Depends(get_current_user)):
#     companies = []
#     cursor = database.admin_companies.find({"created_by": str(current_admin["_id"])})
#     async for doc in cursor:
#         doc["id"] = str(doc["_id"])
#         companies.append(doc)
#     return companies

# @admin_company_router.get("/", response_model=list[AdminCompanyResponse])
# async def get_all_admin_companies(current_admin=Depends(get_current_user)):
#     companies = []
#     cursor = database.admin_companies.find({"created_by": str(current_admin["_id"])})
#     async for doc in cursor:
#         doc["id"] = str(doc["_id"])
#         companies.append(doc)
#     return companies

# @admin_company_router.delete("/{company_id}")
# async def delete_admin_company(company_id: str, current_admin=Depends(get_current_user)):
#     result = await database.admin_companies.delete_one({
#         "_id": ObjectId(company_id),
#         "created_by": str(current_admin["_id"])
#     })
#     if result.deleted_count == 0:
#         raise HTTPException(status_code=404, detail="Company not found or unauthorized")
#     return {"status": "success", "message": "Company deleted"}

