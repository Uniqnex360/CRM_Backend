from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from bson import ObjectId
from database import database
import os
import hashlib

SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 90

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# MAX_BCRYPT_CHARS = 72 

# def hash_password(password: str):
#     truncated = password[:MAX_BCRYPT_CHARS]
#     return pwd_context.hash(truncated)

# def verify_password(plain_password: str, hashed_password: str):
#     truncated = plain_password[:MAX_BCRYPT_CHARS]
#     return pwd_context.verify(truncated, hashed_password)

def hash_password(password: str):
    sha_password = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.hash(sha_password)


def verify_password(plain_password: str, hashed_password: str):
    sha_password = hashlib.sha256(plain_password.encode()).hexdigest()
    return pwd_context.verify(sha_password, hashed_password)



def create_access_token(user_id: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    try:
        obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid user ID")

    user = await database.users.find_one({"_id": obj_id})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

async def authenticate_user(email: str, password: str):
    user = await database.users.find_one({"email": email})
    if not user:
        return False
    if not verify_password(password, user["password"]):
        return False
    return user
