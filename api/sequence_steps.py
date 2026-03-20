from database import database
from fastapi import APIRouter,HTTPException,Depends
from bson import ObjectId
from schemas.steps_schema import StepCreate,StepResponse

steprouter=APIRouter(prefix="/steps",tags=["steps"])
@steprouter.post("/create-steps")
async def create_steps(step:StepCreate):

    sequence_id = ObjectId(step.sequence_id)
    last_step = await database.sequence_steps.find({
        "sequence_id": sequence_id
    }).sort("step_order", -1).limit(1).to_list(length=1)

    next_order = last_step[0]["step_order"] + 1 if last_step else 1

    step_dict = step.dict()

    step_dict["sequence_id"] = sequence_id
    step_dict["step_order"] = next_order   

    step_dict["delay_in_minutes"] = step.get_total_delay_minutes()

    result = await database.sequence_steps.insert_one(step_dict)

    return {
        "message": "Step added",
        "step_order": next_order,
        "id": str(result.inserted_id)
    }


@steprouter.get("/get-steps/{sequence_id}")
async def get_steps(sequence_id: str):

    sequence_id = ObjectId(sequence_id)

    steps = await database.sequence_steps.find({
    "sequence_id": sequence_id}).sort("step_order", 1).to_list(length=100)

    for step in steps:
        step["id"] = str(step["_id"])
        step.pop("_id")

    return steps      

@steprouter.delete("/delete-step/{id}")
async def delete_step(id: str):

    if not ObjectId.is_valid(id):
        raise HTTPException(400, "Invalid step id")

    step = await database.sequence_steps.find_one({"_id": ObjectId(id)})

    if not step:
        raise HTTPException(404, "Step not found")

    sequence_id = step["sequence_id"]

    await database.sequence_steps.delete_one({"_id": ObjectId(id)})
    steps = await database.sequence_steps.find({
        "sequence_id": sequence_id
    }).sort("step_order", 1).to_list(length=100)

    for index, s in enumerate(steps, start=1):
        await database.sequence_steps.update_one(
            {"_id": s["_id"]},
            {"$set": {"step_order": index}}
        )

    return {"message": "Step deleted and reordered"}