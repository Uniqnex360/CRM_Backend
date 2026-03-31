from fastapi import APIRouter, HTTPException,Depends
from bson import ObjectId
from database import database
from schemas.user_schema import UserCreate, UserResponse, UserUpdate
from auth.create_access import get_current_user,super_admin_required,admin_or_super_admin_required
from auth.create_access import hash_password



user_router = APIRouter(prefix="/user",tags=['user'])
def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user.get("name"),
        "email": user.get("email"),
        "tenant_id": str(user.get("tenant_id")) if user.get("tenant_id") else None,
        "role": str(user.get("role")) if user.get("role") else None  
    }

# def user_helper(user) -> dict:
#     return {
#         "id": str(user["_id"]),
#         "name": user["name"],
#         "email": user["email"]
#     }


@user_router.get("/view", response_model=list[UserResponse])
async def view_users(current_user=Depends(admin_or_super_admin_required)):
    query = {}
    if current_user["role"] == "admin":
      tenant_id = current_user.get("tenant_id")

    if current_user["role"] == "admin" and tenant_id:
       if isinstance(tenant_id, ObjectId):
           query["tenant_id"] = tenant_id
       else:
           query["tenant_id"] = ObjectId(tenant_id)

    users = []
    async for user in database.users.find(query):
        print("RAW USER FROM DB:", user) 
        users.append(user_helper(user))
    return users



@user_router.get("/users/{id}", response_model=UserResponse)
async def get_user(id: str,current_user=Depends(super_admin_required)):

    user = await database.users.find_one({"_id": ObjectId(id)})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user_helper(user)



@user_router.put("/users/{id}", response_model=UserResponse)
async def update_user(id: str, user: UserUpdate,current_user=Depends(super_admin_required)):

    await database.users.update_one(
        {"_id": ObjectId(id)},
        {"$set": user.dict()}
    )

    updated_user = await database.users.find_one({"_id": ObjectId(id)})

    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return user_helper(updated_user)


@user_router.delete("/users/{id}")
async def delete_user(id: str,current_user=Depends(super_admin_required)):

    result = await database.users.delete_one({"_id": ObjectId(id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted successfully"}

@user_router.get("/email-count")
async def email_count(current_user=Depends(super_admin_required)):

    pipeline = [
        {
            "$group": {
                "_id": "$user_id",
                "total_emails": {"$sum": 1}
            }
        }
    ]

    result = []
    async for doc in database.email_jobs.aggregate(pipeline):
        result.append({
            "user_id": doc["_id"],
            "total_emails": doc["total_emails"]
        })

    return result


@user_router.post("/create-admin", response_model=UserResponse)
async def create_admin(user: UserCreate, current_user=Depends(admin_or_super_admin_required)):
    existing_user = await database.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    tenant_id = user.tenant_id or current_user.get("tenant_id")
    
    if current_user["role"] == "admin":
      
            if str(tenant_id) != str(current_user["tenant_id"]):
                   raise HTTPException(
                        status_code=403,
                        detail="Cannot assign admin outside your tenant"
        )
        
    if user.role not in ["admin", "user"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    

    hashed_password = hash_password(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    user_dict["tenant_id"] = ObjectId(user_dict["tenant_id"])
    
    result = await database.users.insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id)
    return user_dict

@user_router.put("/promote-admin/{user_id}", response_model=UserResponse)
async def promote_to_admin(user_id: str, current_user=Depends(admin_or_super_admin_required)):
    user = await database.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user["role"] == "admin" and user["tenant_id"] != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Cannot promote user outside your tenant")

    await database.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": "admin"}}
    )
    updated_user = await database.users.find_one({"_id": ObjectId(user_id)})
    return user_helper(updated_user)


@user_router.get("/dashboard")
async def get_dashboard(current_user=Depends(get_current_user)):

    user_id = ObjectId(current_user["id"])
    tenant_id = ObjectId(current_user.get("tenant_id"))
    if current_user["role"] == "admin":
        match_filter = {"tenant_id": tenant_id}
    else:
        match_filter = {"user_id": user_id}


    leads_pipeline = [
        {"$match": match_filter},
        {
            "$facet": {

                "total_leads": [
                    {"$count": "count"}
                    
                    
                ],"leads": [
                {
                    "$project": {
                        "id": {"$toString": "$_id"},
                        "name": 1,
                        "_id": 0
                    }
                }
            ],

              "industry_outreach": [
                 {
                     "$group": {
                         "_id": "$industry",
                         "count": {"$sum": 1}
                     }
                 },
                 {
                     "$project": {
                         "industry_name": "$_id",
                         "count": 1,
                         "_id": 0
                     }
                 }
                 ],
                "location_outreach": [
                    {
                        "$group": {
                            "_id": "$location",
                            "count": {"$sum": 1}
                        }
                    },{
                         "$project": {
                             "location": "$_id",  
                             "count": 1,
                             "_id": 0              
                         }
                     }
                ],

                "companies_reached": [
                              {
                      "$group": {
                          "_id": "$company_name",
                          "count": { "$sum": 1 }
                      }
                  },
                  {
                      "$project": {
                          "company_name": "$_id",
                          "count": 1,
                          "_id": 0
                      }
                  }
              ]
            }
        }
    ]

    leads_result = await database.leads.aggregate(leads_pipeline).to_list(1)
   
    if current_user["role"] == "admin":
        users = await database.users.find(
        {"tenant_id": ObjectId(current_user["tenant_id"])},
        {"_id": 1}
    ).to_list(None)

        user_ids = [str(u["_id"]) for u in users]

        match_filter = {
         "user_id": {"$in": user_ids}   
    }
    else:
            match_filter = {
        "created_by": ObjectId(current_user["id"])
    }

    email_pipeline = [
        {"$match": match_filter},
        {
            "$facet": {

                "total_emails": [
                    {"$count": "count"}
                ],

                "subject_outreach": [
                    {
                        "$group": {
                            "_id": "$subject",
                            "count": {"$sum": 1}
                        }
                    }
                ]
            }
        }
    ]

    email_result = await database.email_jobs.aggregate(email_pipeline).to_list(1)

    users_count = 0
    if current_user["role"] == "admin":
        users_count = await database.users.count_documents({
            "tenant_id": tenant_id,
              "role": "user" 
        })

    return {
        "leads": leads_result[0] if leads_result else {},
        "emails": email_result[0] if email_result else {},
        "Total_users": users_count
    }