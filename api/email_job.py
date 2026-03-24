from fastapi import UploadFile, File, Form
from typing import List,Optional
from fastapi import APIRouter,HTTPException,Depends
from bson import ObjectId
from database import database
from services.email_service import send_email
from datetime import timedelta,datetime,timezone
from zoneinfo import ZoneInfo
from fastapi import Query

email_router=APIRouter(prefix="/email",tags=["email"])



@email_router.post("/create-job")
async def create_email_job(
    sequence_id: str,
    schedule_id: str,
    lead_id: Optional[str] = Query(None),
    list_id: Optional[str] = Query(None)
):

    if not lead_id and not list_id:
        raise HTTPException(status_code=400, detail="Provide either lead_id or list_id")

    if lead_id and list_id:
        raise HTTPException(status_code=400, detail="Provide only one")

    sequence_id = ObjectId(sequence_id)
    schedule_id = ObjectId(schedule_id)

    leads = []


    if lead_id:
        lead = await database.leads.find_one({"_id": ObjectId(lead_id)})
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        leads.append(lead)
    if list_id:
        list_id = ObjectId(list_id)

        members = await database.list_members.find({
            "list_id": list_id
        }).to_list(length=1000)

        if not members:
            raise HTTPException(status_code=404, detail="No members in list")

        for member in members:

            if member["entity_type"] == "people":
                lead = await database.leads.find_one({
                    "_id": member["entity_id"]
                })
                if lead:
                    leads.append(lead)

            elif member["entity_type"] == "company":
                company_leads = await database.leads.find({
                    "company_id": member["entity_id"]
                }).to_list(length=1000)

                leads.extend(company_leads)


    unique_leads = {str(l["_id"]): l for l in leads}
    leads = list(unique_leads.values())

    if not leads:
        raise HTTPException(status_code=404, detail="No valid leads found")
    steps = await database.sequence_steps.find({
        "sequence_id": sequence_id
    }).sort("step_order", 1).to_list(length=100)

    if not steps:
        raise HTTPException(status_code=400, detail="No steps found")

    now = datetime.utcnow()
    jobs = []
    for lead in leads:
        total_delay = 0

        lead_email = lead.get("email") or lead.get("email_id")
        if not lead_email:
            continue

        for step in steps:
            total_delay += step.get("delay_in_minutes", 0)
            send_time = now + timedelta(minutes=total_delay)

            jobs.append({
                "sequence_id": sequence_id,
                "schedule_id": schedule_id,
                "lead_id": lead["_id"],
                "lead_email": lead_email,
                "step_order": step["step_order"],
                "subject": step.get("subject"),
                "body": step.get("body"),
                "scheduled_time": send_time,
                "status": "pending",
                "created_at": now
            })

    if jobs:
        await database.email_jobs.insert_many(jobs)

    return {
        "message": f"{len(jobs)} jobs created",
        "leads_processed": len(leads)
    }

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

            response= await send_email(
                to_email=job["lead_email"],
                subject=job["subject"],
                html_content=job["body"]
            )
            print("BREVO RESPONSE:", response)
            message_id = None

            if response:
                 message_id = response.get("message-id")

            if message_id:
                   message_id = message_id.strip("<>")
                   print("message_id:",message_id)
            await database.email_jobs.update_one(
                {"_id": job["_id"]},
                {"$set": {"status": "sent","message_id": message_id}}
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