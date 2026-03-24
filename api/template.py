from typing import Literal,List
from fastapi import APIRouter,HTTPException,Depends
from datetime import datetime
from bson import ObjectId
from database import database
from bson.errors import InvalidId
from auth.create_access import get_current_user
from schemas.template_schema import TemplateCreate,TemplateResponse,TemplateUpdate
from datetime import datetime, timedelta
from fastapi import Query,Body
template_router=APIRouter(prefix="/template",tags=["template"])

@template_router.post("/create")
async def create_template(
    type: Literal["industry", "platform"] = Query(...),
    data: TemplateCreate = Body(...), current_user=Depends(get_current_user)
):
    template = {
        "template_name": data.template_name,
        "description": data.description,
        "owner_id": str(current_user["_id"]),
        "type": type,             
        "subject": data.subject,        
        "body": data.body,              
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    result = await database.templates.insert_one(template)

    new_template = await database.templates.find_one(
        {"_id": result.inserted_id}
    )

    new_template["id"] = str(new_template["_id"])
    new_template.pop("_id")

    return new_template



@template_router.get("/view_template",response_model=List[TemplateResponse])
async def view_template(current_user=Depends(get_current_user)):
     template=[]
     result=database.templates.find({"owner_id": str(current_user["_id"])})

     async for doc in result:
           doc["id"] = str(doc["_id"])
           doc.pop("_id")
           template.append(doc)

     return template



@template_router.get("/read/{template_id}",response_model=TemplateResponse)
async def read_template(template_id:str,current_user=Depends(get_current_user)):
    try:
        object_id = ObjectId(template_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    
    
    template = await database.templates.find_one({
        "_id": object_id,
        "owner_id": str(current_user["_id"])
      
    })

    if not template:
        raise HTTPException(status_code=404, detail="template not found")

    template["id"] = str(template["_id"])
    del template["_id"]

    return template

@template_router.put("/update/{template_id}")
async def update_template(
    template_id: str,
    data: TemplateUpdate,
    current_user=Depends(get_current_user)
):

    if not ObjectId.is_valid(template_id):
        raise HTTPException(status_code=400, detail="Invalid template id")

    update_data = {
        k: v for k, v in data.dict().items()
        if v is not None and k != "type"
    }
 
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_data["updated_at"] = datetime.utcnow()

    result = await database.templates.update_one(
        {
            "_id": ObjectId(template_id),
            "owner_id": str(current_user["_id"])
        },
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")

    updated_template = await database.templates.find_one(
        {"_id": ObjectId(template_id)}
    )

    updated_template["id"] = str(updated_template["_id"])
    updated_template.pop("_id")

    return updated_template


@template_router.delete("/delete/{template_id}")
async def delete_schedule(
    template_id: str,
    current_user=Depends(get_current_user)
):
  
    try:
        schedule_object_id = ObjectId(template_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    result = await database.templates.delete_one({
        "_id": schedule_object_id,
        "owner_id": str(current_user["_id"])
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="template not found")

    return {"message": "Template deleted successfully"}