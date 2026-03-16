from typing import List
from fastapi import APIRouter,HTTPException,Depends
from datetime import datetime
from bson import ObjectId
from database import database
from bson.errors import InvalidId
from auth.create_access import get_current_user
from schemas.sequence_schema import CreateSequence,SequenceResponse,SequenceUpdate,SequenceStatus

sequence_router=APIRouter(prefix="/sequence",tags=["sequence"])


@sequence_router.post("/create_sequence")
async def create_sequence(data:CreateSequence,
                          current_user=Depends(get_current_user)):
    
    

     sequence={
        "name": data.name,
        "description": data.description,
        "owner_id": str(current_user["_id"]),
        "is_active":data.is_active,
        "is_template":data.is_template,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
     
     result=await database.sequence.insert_one(sequence)

     new_sequence=await database.sequence.find_one({"_id": result.inserted_id})

 
     new_sequence["id"] = str(new_sequence["_id"])
     new_sequence.pop("_id")

     return new_sequence


@sequence_router.get("/view_sequence",response_model=List[SequenceResponse])
async def view_sequence(current_user=Depends(get_current_user)):
     sequence=[]
     cursor=database.sequence.find({"owner_id": str(current_user["_id"]),"is_active": True})

     async for doc in  cursor:
           doc["id"] = str(doc["_id"])
           doc.pop("_id")
           sequence.append(doc)

     return sequence


@sequence_router.get("/view_sequence/{seq_id}",response_model=SequenceResponse)
async def read_sequence(seq_id:str,current_user=Depends(get_current_user)):
    try:
        object_id = ObjectId(seq_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid sequence ID format")

    sequence = await database.sequence.find_one({
        "_id": object_id,
        "owner_id": str(current_user["_id"])
      
    })

    if not sequence:
        raise HTTPException(status_code=404, detail="sequence not found")

    sequence["id"] = str(sequence["_id"])
    del sequence["_id"]

    return sequence

@sequence_router.put("/update_sequence/{seq_id}")
async def update_sequence(
    seq_id: str,
    payload:SequenceUpdate,
    current_user=Depends(get_current_user)):

    seq_object_id = ObjectId(seq_id)

    update_data = payload.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updated_at"] = datetime.utcnow()

    result = await database.sequence.update_one(
        {
            "_id": seq_object_id,
            "owner_id": str(current_user["_id"]),
            "is_active":True
        },
        {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="sequence not found")
    
    updated_sequence = await database.sequence.find_one({"_id": seq_object_id})

    updated_sequence["_id"] = str(updated_sequence["_id"])


    return {"message": "sequence updated successfully"," updated_sequence": updated_sequence}  

@sequence_router.patch("/seq_status/{seq_id}")
async def seq_status(seq_id:str, payload:SequenceStatus,current_user=Depends(get_current_user)):
    result =await database.sequence.update_one(
        {
            "_id": ObjectId(seq_id),
            "owner_id": str(current_user["_id"]),
        },
        {
            "$set": {
                "is_active": payload.is_active,
                "updated_at": datetime.utcnow()
            }   
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sequence not found")

    return {"message": "Sequence status updated successfully"}