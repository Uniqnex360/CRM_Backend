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

# #     return {"status": "ok"}
#     return {
#         "status": "success",
#         "event": event,
#         "message_id": message_id,
#         "job_id": str(job["_id"])
#     }
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