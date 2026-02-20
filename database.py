from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL not found in .env")


database: AsyncIOMotorDatabase = AsyncIOMotorClient(DATABASE_URL).crm_db


async def get_database() -> AsyncIOMotorDatabase:
    return database