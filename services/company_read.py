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

#     return {}


# def build_company_pipeline(filters, current_user):
#     tenant_id = str(current_user.get("tenant_id")) if current_user.get("tenant_id") else None
#     pipeline = []

#     if current_user["role"] == "super_admin":
#         final_match = filters if filters else {}
#     else:
#         tenant_filter = {"$or": [{"tenant_id": ObjectId(tenant_id)}, {"is_global": True}]}
#         if filters and "$and" in filters:
#             final_match = {"$and": filters["$and"] + [tenant_filter]}
#         else:
#             final_match = tenant_filter

#     pipeline.append({"$match": final_match})

    
#     if current_user["role"] == "super_admin":
#         lead_match = {"$expr": {"$eq": ["$company_id", {"$toString": "$$companyId"}]}}
#     else:
#         lead_match = {
#             "$and": [
#                 {"$expr": {"$eq": ["$company_id", {"$toString": "$$companyId"}]}},
#                 {"$or": [{"tenant_id": tenant_id}, {"is_global": True}]}
#             ]
#         }

#     pipeline.append({
#         "$lookup": {
#             "from": "leads",
#             "let": {"companyId": "$_id"},
#             "pipeline": [{"$match": lead_match}, {"$limit": 5}],
#             "as": "leads"
#         }
#     })

#     # Sort
#     pipeline.append({"$sort": {"company_name": 1}})

#     return pipeline
