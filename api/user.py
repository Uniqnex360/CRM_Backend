from fastapi import APIRouter, HTTPException,Depends
from bson import ObjectId
from database import database
from schemas.user_schema import UserCreate, UserResponse, UserUpdate
from auth.create_access import get_current_user,admin_required




user_router = APIRouter(prefix="/user",tags=['user'])


def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"]
    }


@user_router.get("/view", response_model=list[UserResponse])
async def view_users(current_user=Depends(admin_required)):

    users = []
    async for user in database.users.find():
        users.append(user_helper(user))

    return users



@user_router.get("/users/{id}", response_model=UserResponse)
async def get_user(id: str,current_user=Depends(admin_required)):

    user = await database.users.find_one({"_id": ObjectId(id)})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user_helper(user)



@user_router.put("/users/{id}", response_model=UserResponse)
async def update_user(id: str, user: UserUpdate,current_user=Depends(admin_required)):

    await database.users.update_one(
        {"_id": ObjectId(id)},
        {"$set": user.dict()}
    )

    updated_user = await database.users.find_one({"_id": ObjectId(id)})

    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return user_helper(updated_user)


@user_router.delete("/users/{id}")
async def delete_user(id: str,current_user=Depends(admin_required)):

    result = await database.users.delete_one({"_id": ObjectId(id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted successfully"}

@user_router.get("/email-count")
async def email_count(current_user=Depends(admin_required)):

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
