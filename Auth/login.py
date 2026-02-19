from fastapi import APIRouter, Depends,HTTPException
from Auth.create_access import authenticate_user, create_access_token,get_current_user
from fastapi.security import OAuth2PasswordRequestForm

login_router = APIRouter()

@login_router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(str(user["_id"]))
    return {"access_token": access_token, "token_type": "bearer"}

@login_router.get("/me")
async def read_users_me(current_user=Depends(get_current_user)):
    return current_user
