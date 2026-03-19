from fastapi import UploadFile, File, Form
from typing import List
from fastapi import APIRouter,HTTPException,Depends
from bson import ObjectId
from database import database
from services.email_service import send_email
from datetime import timedelta
from datetime import datetime
from zoneinfo import ZoneInfo


email_router=APIRouter(prefix="/email",tags=["email"])
@email_router.post("/create-job")
async def create_email_job(
    sequence_id: str,
    schedule_id: str,
    email: str
):
    await database.email_jobs.insert_one({
        "sequence_id":ObjectId(sequence_id),
        "schedule_id": ObjectId(schedule_id),
        "email": email,
        "status": "pending",
        "scheduled_at": datetime.utcnow() - timedelta(minutes=1),
        "created_at": datetime.utcnow()
    })

    return {"message": "Email job created"}

async def process_sequences():
    # now = datetime.utcnow()
    now = datetime.now(ZoneInfo("UTC"))
    # print(now,"now")

    runs = database.email_jobs.find({
        "scheduled_at": {"$lte": now},
        "status": "pending"
    })
    # print(runs,"runs")
     
    async for run in runs:
    
        # print("Sending to:", run["email"])
        schedule = await database.schedule.find_one({"_id": ObjectId(run["schedule_id"])})
        # print("RAW run document:", run)
        # print("schedule_id value:", run.get("schedule_id"))
        # print("schedule_id type:", type(run.get("schedule_id")))

        if not schedule:
            # print(type(schedule),"schedule_type")
            # print("No schedule found, skipping")
            continue
        tz = ZoneInfo(schedule["timezone"])
        now_local = now.astimezone(tz)
     

        current_day = now_local.strftime("%A").lower()
        current_time = now_local.strftime("%H:%M")
        # print("Day:", current_day)
        # print("Time:", current_time)
        # print("Job schedule_id:", run["schedule_id"])
        # print("Type:", type(run["schedule_id"]))
        windows = schedule["sending_windows"].get(current_day, [])
        allowed = False
        for window in windows:
            if window["start"] <= current_time <= window["end"]:
                allowed = True
                break

        if not allowed:
            print(f"Not allowed now ({current_day} {current_time}), skipping")
            await database.email_jobs.update_one(
                {"_id": run["_id"]},
                {
                    "$set": {
                        "scheduled_at": now + timedelta(minutes=10)
                    }
                }
            )
            continue
        try:
            await send_email(
                to_email=run["email"],
                subject="Test Email",
                html_content="<h1>Hello from CRM</h1>"
            )

            await database.email_jobs.update_one(
                {"_id": run["_id"]},
                {
                    "$set": {
                        "status": "sent",
                        "sent_at": now
                    }
                }
            )
            # print("UTC:", now)
            # print("Local:", now_local)
            
        except Exception as e:
            print("Error:", str(e))

            await database.email_jobs.update_one(
                {"_id": run["_id"]},
                {
                    "$set": {
                        "status": "failed",
                        "error": str(e)
                    }
                }
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