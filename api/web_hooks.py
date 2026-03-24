from fastapi import APIRouter
from datetime import datetime
from database  import database 
webhook_router = APIRouter(prefix="/webhook", tags=["webhook"])


@webhook_router.post("/brevo")
async def brevo_webhook(payload: dict):

    event = payload.get("event")
    print(event,"Event")
    message_id = payload.get("message-id")

    if message_id:
        message_id = message_id.strip("<>")
    print(message_id,"Message_id")

    if not message_id:
        return {"status": "ignored"}

    job = await database.email_jobs.find_one({
        "message_id": message_id
    })
    print("job",job)

    if not job:
        return {"status": "not_found"}
    
    if event == "delivered":
        await database.email_jobs.update_one(
            {"_id": job["_id"]},
            {"$set": {"status": "delivered"}}
        )

    elif event == "open":
        await database.email_jobs.update_one(
            {"_id": job["_id"]},
            {"$set": {"opened": True, "opened_at": datetime.utcnow()}}
        )

    elif event == "click":
        await database.email_jobs.update_one(
            {"_id": job["_id"]},
            {"$inc": {"click_count": 1}}
        )

    elif event == "bounce":
        await database.email_jobs.update_one(
            {"_id": job["_id"]},
            {"$set": {"status": "failed"}}
        )

    return {"status": "ok"}