from fastapi import APIRouter, Depends,HTTPException
from Auth.create_access import authenticate_user, create_access_token,get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from schemas.user_schema import UserCreate,UserResponse,UserUpdate
from database import database
from Auth.create_access import create_access_token,hash_password
auth_router = APIRouter(tags=['auth'])


def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"]
    }

@auth_router.post("/signup", response_model=UserResponse)



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

@auth_router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(str(user["_id"]))
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.get("/me")
async def read_users_me(current_user=Depends(get_current_user)):
    return current_user



@auth_router.post("/logout")
async def user_logout(current_user=Depends(get_current_user)):
    return {"message": "Logout successful."}