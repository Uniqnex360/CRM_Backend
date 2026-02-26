from fastapi import APIRouter, HTTPException,Depends
from bson import ObjectId
from database import database
from schemas.user_schema import UserCreate, UserResponse, UserUpdate
from auth.create_access import get_current_user
from auth.create_access import hash_password



user_router = APIRouter(tags=['user'])


def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"]
    }


@user_router.get("/users", response_model=list[UserResponse])
async def view_users(current_user=Depends(get_current_user)):

    users = []
    async for user in database.users.find():
        users.append(user_helper(user))

    return users



@user_router.get("/users/{id}", response_model=UserResponse)
async def get_user(id: str,current_user=Depends(get_current_user)):

    user = await database.users.find_one({"_id": ObjectId(id)})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user_helper(user)



@user_router.put("/users/{id}", response_model=UserResponse)
async def update_user(id: str, user: UserUpdate,current_user=Depends(get_current_user)):

    await database.users.update_one(
        {"_id": ObjectId(id)},
        {"$set": user.dict()}
    )

    updated_user = await database.users.find_one({"_id": ObjectId(id)})

    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return user_helper(updated_user)


@user_router.delete("/users/{id}")
async def delete_user(id: str,current_user=Depends(get_current_user)):

    result = await database.users.delete_one({"_id": ObjectId(id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted successfully"}
