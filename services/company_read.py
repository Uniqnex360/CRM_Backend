from utils.clean_data import normalize_fuzzy_regex_safe,normalize_fuzzy_regex
from auth.create_access import get_current_user
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
            "location": {
                "$regex": normalize_fuzzy_regex(location),
                "$options": "i"
            }
        })

    if employee_count and employee_count.strip():
        filters.append({
            "employee_size": {
                "$regex":  rf"\b{employee_count}\b",
                "$options": "i"
            }
        })

    if revenue and revenue.strip():
        filters.append({
            "gross_revenue": {
                "$regex": rf"\b{revenue}\b",
                "$options": "i"
            }
        })
    if filters:
        return {"$and": filters}

    return {}

# def build_company_pipeline(filters, skip, limit,current_user):
#     access_filter = {
#     "$or": [
#         {"company_id":str(current_user["company_id"])}, 
#         # {"is_global": True}  
#         ]}
#     pipeline = []

#     if filters:
#         pipeline.append({"$match": {
#         "$and": [filters, access_filter]}
#     })
#     else:
#           pipeline.append({
#         "$match": access_filter
#     })

#     pipeline.append({
#         "$lookup": {
#             "from": "leads",
#             "let": {"companyId": "$_id"},
#             "pipeline": [
#                 {
#                     "$match": {
#                         "$expr": {
#                             "$eq": [
#                                "$company_id",
#                                {"$toString": "$$companyId"}]
#                         }
#                     }
#                 },
#                 {
#                     "$project": {
#                         "name": 1,
#                         "title": 1,
#                         "primary_number": 1,
#                         "personal_linkedin_source": 1,
#                         "email_id":1
#                     }
#                 },
#                 {"$limit": 5}
#             ],
#             "as": "leads"
#         }
#     })

#     pipeline.append({"$sort": {"company_name": 1}})
#     pipeline.append({"$skip": skip})
#     pipeline.append({"$limit": limit})

#     return pipeline

def build_company_pipeline(filters, skip, limit, current_user):

    access_filter = {
        "tenant_id": str(current_user["tenant_id"])
    }
    if filters and "$and" in filters:
        final_match = {
            "$and": filters["$and"] + [access_filter]
        }
    else:
        final_match = access_filter
    pipeline = []

    pipeline.append({
        "$match": final_match
    })

    pipeline.append({
        "$lookup": {
            "from": "leads",
            "let": {"companyId": "$_id"},
            "pipeline": [
                {
                    "$match": {
                        "$and": [
                            {
                                "$expr": {
                                    "$eq": [
                                        "$company_id",
                                        {"$toString": "$$companyId"}
                                    ]
                                }
                            },
                            {
                                "tenant_id": str(current_user["tenant_id"])
                            }
                        ]
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