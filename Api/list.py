import json
from fastapi import UploadFile, File, Form
from typing import Optional
from fastapi import APIRouter,HTTPException,Depends
from datetime import datetime
from bson import ObjectId
from database import database
from pydantic import BaseModel

from schemas.list_schema import ListBase,ListCreate,ListMemberCreate,ListResponse
from auth.create_access import get_current_user

list_router=APIRouter(prefix="/list",tags=["list"])

@list_router.post("/create_list", response_model=ListResponse)
async def create_list(
    data: ListCreate,
    current_user=Depends(get_current_user)
):
    now = datetime.utcnow()

    list_doc = {
        "list_name": data.list_name,
        "description": data.description,
        "type": data.type,
        "owner_id": str(current_user["_id"]),
        "created_at": now,
        "updated_at": now
    }

    result = await database.lists.insert_one(list_doc)

    return result