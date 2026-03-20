from fastapi import UploadFile, File, Form
from typing import List
from fastapi import APIRouter,HTTPException,Depends
from bson import ObjectId
from database import database
from services.email_service import send_email
from datetime import timedelta,datetime,timezone
from zoneinfo import ZoneInfo


email_router=APIRouter(prefix="/email",tags=["email"])



# @email_router.post("/create-job")
# async def create_email_job(
#     sequence_id: str,
#     schedule_id: str,
#     lead_id: str
# ):
#     await database.email_jobs.insert_one({
#         "sequence_id":ObjectId(sequence_id),
#         "schedule_id": ObjectId(schedule_id),
#         "email": ObjectId(lead_id),
#         "status": "pending",
#         "scheduled_at": datetime.utcnow() - timedelta(minutes=1),
#         "created_at": datetime.utcnow()
#     })

#     return {"message": "Email job created"}
@email_router.post("/create-job")
async def create_email_job(sequence_id: str, schedule_id: str, lead_id: str):

    sequence_id = ObjectId(sequence_id)
    schedule_id = ObjectId(schedule_id)
    lead_id = ObjectId(lead_id)

 
    lead = await database.leads.find_one({"_id": lead_id})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    steps = await database.sequence_steps.find({
        "sequence_id": sequence_id
    }).sort("step_order", 1).to_list(length=100)

    if not steps:
        raise HTTPException(status_code=400, detail="No steps found")

    now = datetime.utcnow()
    total_delay = 0

    jobs = []

    for step in steps:
        total_delay += step.get("delay_in_minutes", 0)

        send_time = now + timedelta(minutes=total_delay)

        jobs.append({
            "sequence_id": sequence_id,
            "schedule_id": schedule_id,
            "lead_id": lead_id,
            "lead_email": lead["email_id"],   
            "step_order": step["step_order"],
            "subject": step.get("subject"),
            "body": step.get("body"),
            "scheduled_time": send_time,   
            "status": "pending",
            "created_at": now
        })

    if jobs:
        await database.email_jobs.insert_many(jobs)

    return {"message": f"{len(jobs)} jobs created"}



async def process_sequences():

    now = datetime.utcnow()

    jobs = database.email_jobs.find({
        "status": "pending",
        "scheduled_time": {"$lte": now}
    })

    async for job in jobs:

        schedule = await database.schedule.find_one({
            "_id": ObjectId(job["schedule_id"])
        })

        if not schedule:
            continue

        tz = ZoneInfo(schedule["timezone"])
        now_local = now.astimezone(tz)

        current_day = now_local.strftime("%A").lower()
        current_time = now_local.strftime("%H:%M")

        windows = schedule["sending_windows"].get(current_day, [])

        allowed = any(
            w["start"] <= current_time <= w["end"]
            for w in windows
        )

        if not allowed:
            continue

        try:
            await send_email(
                to_email=job["lead_email"],
                subject=job["subject"],
                html_content=job["body"]
            )

            await database.email_jobs.update_one(
                {"_id": job["_id"]},
                {"$set": {"status": "sent"}}
            )

        except Exception as e:
            await database.email_jobs.update_one(
                {"_id": job["_id"]},
                {"$set": {"status": "failed", "error": str(e)}}
            )
@email_router.post("/run-sequences")
async def run_sequences():
    await process_sequences()
    return {"status": "processed"}



# import asyncio

# async def scheduler_loop():
#     while True:
#         print("Running scheduler...",datetime.utcnow())
#         await process_sequences()
#         await asyncio.sleep(300)  


# @email_router.get("/test-email")
# async def test_email():
#     await send_email(
#         subject="Test Email",
#         html_content="<h1>Hiii</h1>"
#     )
#     return {"message": "sent"}