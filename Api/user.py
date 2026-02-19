from fastapi import APIRouter, HTTPException,Depends
from bson import ObjectId
from database import database
from schemas.user_schema import UserCreate, UserResponse, UserUpdate
from Auth.create_access import get_current_user
from Auth.create_access import hash_password
user_router = APIRouter()


def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"]
    }



@user_router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate):

    existing_user = await database.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password) 
    print(user_dict)

    result = await database.users.insert_one(user_dict)
    created_user = await database.users.find_one({"_id": result.inserted_id})

    return user_helper(created_user)



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
