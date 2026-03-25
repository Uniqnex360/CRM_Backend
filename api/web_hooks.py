from fastapi import APIRouter
from datetime import datetime
from database  import database 
webhook_router = APIRouter(prefix="/webhook", tags=["webhook"])

@webhook_router.post("/brevo")
async def brevo_webhook(payload: dict):

    event = payload.get("event")
    message_id = payload.get("message-id")

    if not message_id:
        return {"status": "ignored"}

    message_id = message_id.strip("<>")

    job = await database.email_jobs.find_one({"message_id": message_id})

    if not job:
        return {"status": "not_found"}

    update = {}
    if event == "delivered":
        update = {
            "$set": {
                "status": "delivered",
                "delivered_at": datetime.utcnow()
            }
        }
    elif event in ["open", "opened"]:
        update = {
            "$set": {
                "opened": True,
                "opened_at": job.get("opened_at") or datetime.utcnow()
            }
        }
    elif event == "bounce":
        update = {
            "$set": {
                "status": "failed"
            }
        }
    if update:
        await database.email_jobs.update_one(
            {"_id": job["_id"]},
            update
        )

    return {"status": "ok"}