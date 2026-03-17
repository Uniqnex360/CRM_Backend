from fastapi import UploadFile, File, Form
from typing import List
from fastapi import APIRouter,HTTPException,Depends
from datetime import datetime
from bson import ObjectId
from database import database
from pydantic import BaseModel
from bson.errors import InvalidId

from auth.create_access import get_current_user
from schemas.schedule_schema import ScheduleCreate,ScheduleResponse,ScheduleUpdate


schedule_router=APIRouter(prefix="/schedule",tags=["schedule"])

@schedule_router.post("/create_schedule")
async def create_schedule(data:ScheduleCreate,current_user=Depends(get_current_user)):  
    schedule = data.model_dump()
    schedule.update({
        "owner_id": str(current_user["_id"]),
        "is_active":data.is_active,
        "created_at": datetime.utcnow(),
    })
     
    result=await database.schedule.insert_one(schedule)

    new_schedule=await database.schedule.find_one({"_id": result.inserted_id})

 
    new_schedule["id"] = str(new_schedule["_id"])
    new_schedule.pop("_id")

    return new_schedule




@schedule_router.get("/view_schedule",response_model=List[ScheduleResponse])
async def view_schedule(current_user=Depends(get_current_user)):
     schedule=[]
     cursor=database.schedule.find({"owner_id": str(current_user["_id"]),"is_active": True})

     async for doc in  cursor:
           doc["id"] = str(doc["_id"])
           doc.pop("_id")
           schedule.append(doc)

     return schedule


@schedule_router.get("/read_schedule/{schedule_id}",response_model=ScheduleResponse)
async def read_schedule(schedule_id:str,current_user=Depends(get_current_user)):
    try:
        object_id = ObjectId(schedule_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid schedule ID format")

    schedule = await database.schedule.find_one({
        "_id": object_id,
        "owner_id": str(current_user["_id"])
      
    })

    if not schedule:
        raise HTTPException(status_code=404, detail="schedule not found")

    schedule["id"] = str(schedule["_id"])
    del schedule["_id"]

    return schedule


@schedule_router.put("/update_schedule/{sch_id}")
async def update_schedule(
    sch_id: str,
    payload:ScheduleUpdate,
    current_user=Depends(get_current_user)):

    schedule_object_id = ObjectId(sch_id)

    update_data = payload.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updated_at"] = datetime.utcnow()

    result = await database.schedule.update_one(
        {
            "_id": schedule_object_id,
            "owner_id": str(current_user["_id"]),
            "is_active":True
        },
        {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="schedule not found")
    
    updated = await database.schedule.find_one({"_id": schedule_object_id})

    updated["_id"] = str(updated["_id"])


    return {"message": "schedule updated successfully"," updated_sequence": updated}  


@schedule_router.delete("/delete_schedule/{sch_id}")
async def delete_schedule(
    sch_id: str,
    current_user=Depends(get_current_user)
):
    # print(current_user)
    try:
        schedule_object_id = ObjectId(sch_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid schedule ID format")

    result = await database.schedule.delete_one({
        "_id": schedule_object_id,
        "owner_id": str(current_user["_id"])
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return {"message": "Schedule deleted successfully"}