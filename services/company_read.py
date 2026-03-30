from utils.clean_data import normalize_fuzzy_regex_safe,normalize_fuzzy_regex
from auth.create_access import get_current_user
from bson import ObjectId

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
            "industry": {"$regex": normalize_fuzzy_regex_safe(vertical), "$options": "i"}
        })

    if location and location.strip():
        filters.append({
            "location": {"$regex": normalize_fuzzy_regex(location), "$options": "i"}
        })

    if employee_count and employee_count.strip():
        filters.append({
            "employee_size": {"$regex": rf"\b{employee_count}\b", "$options": "i"}
        })

    if revenue and revenue.strip():
        filters.append({
            "gross_revenue": {"$regex": rf"\b{revenue}\b", "$options": "i"}
        })

    if filters:
        return {"$and": filters}

    return {}

