from fastapi import APIRouter
from datetime import datetime
from database  import database 
webhook_router = APIRouter(prefix="/webhook", tags=["webhook"])


# @webhook_router.post("/brevo")
# async def brevo_webhook(payload: dict):

#     event = payload.get("event")
#     print(event,"Event")
#     message_id = payload.get("message-id")

#     if message_id:
#         message_id = message_id.strip("<>")
#     print(message_id,"Message_id")

#     if not message_id:
#         return {"status": "ignored"}

#     job = await database.email_jobs.find_one({
#         "message_id": message_id
#     })
#     print("job",job)

#     if not job:
#         return {"status": "not_found"}
    
#     if event == "delivered":
#         await database.email_jobs.update_one(
#             {"_id": job["_id"]},
#             {"$set": {"status": "delivered"}}
#         )

#     elif event == "open":
#         await database.email_jobs.update_one(
#             {"_id": job["_id"]},
#             {"$set": {"opened": True, "opened_at": datetime.utcnow()}}
#         )

#     elif event == "click":
#         await database.email_jobs.update_one(
#             {"_id": job["_id"]},
#             {"$inc": {"click_count": 1}}
#         )

#     elif event == "bounce":
#         await database.email_jobs.update_one(
#             {"_id": job["_id"]},
#             {"$set": {"status": "failed"}}
#         )

#     return {"status": "ok"}


@webhook_router.post("/brevo")
async def brevo_webhook(payload: dict):

    event = payload.get("event")
    message_id = payload.get("message-id")

    if message_id:
        message_id = message_id.strip("<>")

    if not message_id:
        return {
            "status": "ignored",
            "reason": "missing_message_id"
        }

    job = await database.email_jobs.find_one({
        "message_id": message_id
    })

    if not job:
        return {
            "status": "not_found",
            "message_id": message_id
        }

    update_data = {}
    action = None

    if event in ["delivered"]:
        update_data = {
            "status": "delivered",
            "delivered_at": datetime.utcnow()
        }
        action = "marked_delivered"

    elif event in ["open", "opened"]:
        update_data = {
            "opened": True,
            "opened_at": datetime.utcnow()
        }
        action = "marked_opened"

    elif event in ["click", "clicked"]:
        update_data = {
            "$inc": {"click_count": 1},
            "$set": {"last_clicked_at": datetime.utcnow()}
        }
        action = "click_recorded"

    elif event in ["bounce"]:
        update_data = {
            "status": "failed",
            "bounced_at": datetime.utcnow()
        }
        action = "marked_failed"

    # Handle $inc separately
    if "$inc" in update_data:
        await database.email_jobs.update_one(
            {"_id": job["_id"]},
            update_data
        )
    else:
        await database.email_jobs.update_one(
            {"_id": job["_id"]},
            {"$set": update_data}
        )

    return {
        "status": "success",
        "event": event,
        "action": action,
        "message_id": message_id,
        "job_id": str(job["_id"])
    }