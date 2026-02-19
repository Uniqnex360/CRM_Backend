from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from fastapi import HTTPException

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


if not DATABASE_URL:
    raise HTTPException(status_code=500, detail="DATABASE_URL Not found in .env")


client = AsyncIOMotorClient(DATABASE_URL)
database = client.crm_db


