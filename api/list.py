import json
from fastapi import UploadFile, File, Form
from typing import List
from fastapi import APIRouter,HTTPException,Depends
from datetime import datetime
from bson import ObjectId
from database import database


from schemas.list_schema import ListBase,ListCreate,ListMemberCreate,ListResponse,ListUpdate,RemoveListMembers
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
        "no_of_records": 0,
        "created_at": now,
        "updated_at": now
    }

    result = await database.lists.insert_one(list_doc)

  
    new_list = await database.lists.find_one(
        {"_id": result.inserted_id}
    )

 
    new_list["id"] = str(new_list["_id"])
    new_list.pop("_id")

    return new_list


@list_router.get("/view_lists", response_model=List[ListResponse])
async def view_list(current_user=Depends(get_current_user)):

    result = []

    cursor = database.lists.find({
        "owner_id": str(current_user["_id"])
    })

    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        doc.pop("_id")
        result.append(doc)

    return result

@list_router.post("/{list_id}/add_members")
async def add_members(
    list_id: str,
    payload: ListMemberCreate,
    current_user=Depends(get_current_user)
):
    
    try:
        list_object_id = ObjectId(list_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid list ID")

  
    list_doc = await database.lists.find_one({
        "_id": list_object_id,
        "owner_id": str(current_user["_id"])
    })

    if not list_doc:
        raise HTTPException(status_code=404, detail="List not found")

 
    entity_object_ids = []
    for entity_id in payload.entity_ids:
        try:
            entity_object_ids.append(ObjectId(entity_id))
        except:
            raise HTTPException(status_code=400, detail=f"Invalid entity ID: {entity_id}")


    if list_doc["type"] == "people":
        count = await database.leads.count_documents({
            "_id": {"$in": entity_object_ids}
        })
    else:
        count = await database.company.count_documents({
            "_id": {"$in": entity_object_ids}
        })

    if count != len(entity_object_ids):
        raise HTTPException(status_code=400, detail="Some entity IDs do not exist")

    inserted_count = 0

    for entity_object_id in entity_object_ids:
        existing = await database.list_members.find_one({
            "list_id": list_object_id,
            "entity_id": entity_object_id
        })

        if not existing:
            await database.list_members.insert_one({
                "list_id": list_object_id,
                "entity_id": entity_object_id,
                "entity_type": list_doc["type"],
                "added_at": datetime.utcnow()
            })
            inserted_count += 1

  
    if inserted_count > 0:
        await database.lists.update_one(
            {"_id": list_object_id},
            {
                "$inc": {"no_of_records": inserted_count},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
    if inserted_count == 0:
      return {
        "message": "Already added in the list" }

    return {
        "message": "Members added successfully",
        "added_count": inserted_count
    }

@list_router.get("/{list_id}/view_members")
async def view_members(
    list_id: str,
    current_user=Depends(get_current_user)
):
    try:
        list_object_id = ObjectId(list_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid list ID")

    list_doc = await database.lists.find_one({
        "_id": list_object_id,
        "owner_id": str(current_user["_id"])
    })

    if not list_doc:
        raise HTTPException(status_code=404, detail="List not found")

  
    members_cursor = database.list_members.find({
        "list_id": list_object_id
    })

    members = []
    async for m in members_cursor:

        entity_id = m["entity_id"]

        if list_doc["type"] == "companies":
            entity_doc = await database.company.find_one({"_id": entity_id})
            entity_name = entity_doc.get("company_name") if entity_doc else None
        else:
            entity_doc = await database.leads.find_one({"_id": entity_id})
            entity_name = entity_doc.get("name") if entity_doc else None

        m["id"] = str(m["_id"])
        m["list_id"] = str(m["list_id"])  
        m["entity_id"] = str(m["entity_id"])
        m["entity_name"]=entity_name 
        m.pop("_id")
        members.append(m)

    return {
        "list_name": list_doc["list_name"],
        "type": list_doc["type"],
        "members": members
    }


@list_router.put("/{list_id}")
async def update_list(
    list_id: str,
    payload: ListUpdate,
    current_user=Depends(get_current_user)
):
    list_object_id = ObjectId(list_id)

    update_data = payload.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updated_at"] = datetime.utcnow()

    result = await database.lists.update_one(
        {
            "_id": list_object_id,
            "owner_id": str(current_user["_id"])
        },
        {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="List not found")

    return {"message": "List updated successfully"}

@list_router.delete("/{list_id}/members")
async def remove_members(
    list_id: str,
    payload: RemoveListMembers,
    current_user=Depends(get_current_user)):
    try:
        list_object_id = ObjectId(list_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid list ID")

    list_doc = await database.lists.find_one({
        "_id": list_object_id,
        "owner_id": str(current_user["_id"])
    })

    if not list_doc:
        raise HTTPException(status_code=404, detail="List not found")

  
    entity_object_ids = []

    if payload.entity_id:
        try:
            entity_object_ids.append(ObjectId(payload.entity_id))
        except:
            raise HTTPException(status_code=400, detail="Invalid entity ID")

    elif payload.entity_ids:
        try:
            entity_object_ids = [ObjectId(eid) for eid in payload.entity_ids]
        except:
            raise HTTPException(status_code=400, detail="Invalid entity ID in list")

    else:
        raise HTTPException(
            status_code=400,
            detail="Provide entity_id or entity_ids"
        )

    result = await database.list_members.delete_many({
        "list_id": list_object_id,
        "entity_id": {"$in": entity_object_ids}
    })

    removed_count = result.deleted_count

    if removed_count > 0:
        await database.lists.update_one(
            {"_id": list_object_id},
            {"$inc": {"no_of_records": -removed_count}}
        )

    return {
        "message": "Members removed successfully",
        "removed_count": removed_count
    }

@list_router.delete("/{list_id}")
async def delete_list(
    list_id: str,
    current_user=Depends(get_current_user)):

    try:
        list_object_id = ObjectId(list_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid list ID")
    
    list_doc = await database.lists.find_one({
        "_id": list_object_id,
        "owner_id": str(current_user["_id"])
    })

    if not list_doc:
        raise HTTPException(status_code=404, detail="List not found")

   
    await database.list_members.delete_many({
        "list_id": list_object_id
    })


    await database.lists.delete_one({
        "_id": list_object_id
    })

    return {"message": "List deleted successfully"}