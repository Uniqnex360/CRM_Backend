from fastapi import APIRouter, Depends
from database import database
from services.industry_service import migrate_industries

migrate_router = APIRouter(prefix="/migrate", tags=["industry"])

@migrate_router.post("/industry")
async def migrate_industry_data():
    return await migrate_industries(database)