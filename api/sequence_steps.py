from database import database
from fastapi import APIRouter,HTTPException,Depends
from bson import ObjectId
from schemas.sequence_schema import StepCreate


steprouter=APIRouter(prefix="/steps",tags=["steps"])

@steprouter.post("/create-steps")
async def create_steps(step: StepCreate, database):
          step_dict=step.dict()
          
          existing = await database.sequence_steps.find_one({
        "sequence_id": step.sequence_id,
        "step_number": step.step_number
    })
          if existing:
              raise HTTPException(400, "Step already exists")
          result = await database.sequence_steps.insert_one(step_dict)

          return {"message": "Step added",
        "id": str(result.inserted_id)}


      

@steprouter.delete("/delete-step/{id}")
async def delete_step(id:str,database):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid step id")

    result = await database.sequence_steps.delete_one({
        "_id": ObjectId(id)
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Step not found")

    return {"message": "Step deleted successfully"}