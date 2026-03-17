from fastapi import UploadFile, File, Form
from typing import List
from fastapi import APIRouter,HTTPException,Depends
from bson import ObjectId
from database import database
from services.email_service import send_email
from datetime import timedelta
from datetime import datetime
import pytz

email_router=APIRouter(prefix="/email",tags=["email"])
@email_router.post("/create-job")
async def create_email_job(
    sequence_id: str,
    schedule_id: str,
    email: str
):
    await database.email_jobs.insert_one({
        "sequence_id": sequence_id,
        "schedule_id": schedule_id,
        "email": email,
        "status": "pending",
        "scheduled_at": datetime.utcnow() - timedelta(minutes=1),
        "created_at": datetime.utcnow()
    })

    return {"message": "Email job created"}

async def process_sequences():
    now = datetime.utcnow()


    ist = pytz.timezone("Asia/Kolkata")
    now_ist = now.astimezone(ist)

    print("Current IST time:", now_ist)

    # if now_ist.minute % 5 != 0:
    #     print("Skipping - not a 5 min interval")
    #     return

    runs = database.email_jobs.find({
        "scheduled_at": {"$lte": now},
        "status": "pending"
    })

    async for run in runs:
        print("Processing job:", run["_id"])
        print("Sending to:", run["email"])   
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

import asyncio

async def scheduler_loop():
    while True:
        print("Running scheduler...",datetime.utcnow())
        await process_sequences()
        await asyncio.sleep(300)  


@email_router.post("/run-sequences")
async def run_sequences():
    await process_sequences()
    return {"status": "processed"}

@email_router.get("/test-email")
async def test_email():
    await send_email(
        subject="Test Email",
        html_content="<h1>Hiii</h1>"
    )
    return {"message": "sent"}