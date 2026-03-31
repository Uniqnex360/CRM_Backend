from datetime import datetime

async def migrate_industries(database):

    industries = await database["company"].distinct("industry")

    existing = await database["industry"].distinct("name")

    industry_docs = [
        {
            "name": industry,
            "created_at": datetime.utcnow()
        }
        for industry in industries
        if industry and industry not in existing
    ]

    if not industry_docs:
        return {"message": "No new industries to insert"}

    result = await database["industry"].insert_many(industry_docs)

    return {
        "inserted_ids": [str(_id) for _id in result.inserted_ids]
    }