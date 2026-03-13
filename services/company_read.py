from utils.clean_data import normalize_fuzzy_regex_safe,normalize_fuzzy_regex
def build_company_filters(keyword, vertical, location, employee_count, revenue):
    filters = []

    if keyword and keyword.strip():
        keyword = normalize_fuzzy_regex_safe(keyword.strip())
        filters.append({
            "$or": [
                {"company_name": {"$regex": keyword, "$options": "i"}},
                {"industry": {"$regex": keyword, "$options": "i"}},
                {"domain_url": {"$regex": keyword, "$options": "i"}}
            ]
        })

    if vertical and vertical.strip():
        filters.append({
            "industry": {
                "$regex": normalize_fuzzy_regex_safe(vertical),
                "$options": "i"
            }
        })

    if location and location.strip():
        filters.append({
            "country": {
                "$regex": normalize_fuzzy_regex(location),
                "$options": "i"
            }
        })

    if employee_count and employee_count.strip():
        filters.append({
            "employee_size": {
                "$regex": employee_count.strip(),
                "$options": "i"
            }
        })

    if revenue and revenue.strip():
        filters.append({
            "gross_revenue": {
                "$regex": normalize_fuzzy_regex(revenue),
                "$options": "i"
            }
        })
    if filters:
        return {"$and": filters}

    return {}

def build_company_pipeline(filters, skip, limit):

    pipeline = []

    if filters:
        pipeline.append({
            "$match":filters
        })

    pipeline.append({
        "$lookup": {
            "from": "leads",
            "let": {"companyId": "$_id"},
            "pipeline": [
                {
                    "$match": {
                        "$expr": {
                            "$eq": ["$company_id", "$$companyId"]
                        }
                    }
                },
                {
                    "$project": {
                        "name": 1,
                        "title": 1,
                        "primary_number": 1,
                        "personal_linkedin_source": 1
                    }
                },
                {"$limit": 5}
            ],
            "as": "leads"
        }
    })

    pipeline.append({"$sort": {"company_name": 1}})
    pipeline.append({"$skip": skip})
    pipeline.append({"$limit": limit})

    return pipeline