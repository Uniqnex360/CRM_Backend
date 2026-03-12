from utils.clean_data import normalize_fuzzy_regex_safe
def lead_filters(keyword=None, name=None, title=None, company=None, location=None, industry=None):
    query = {}
    filters = []

    if keyword:
        keyword_regex = normalize_fuzzy_regex_safe(keyword)

        query["$or"] = [
            {"name": {"$regex": keyword_regex, "$options": "i"}},
            {"title": {"$regex": keyword_regex, "$options": "i"}},
            {"industry": {"$regex": keyword_regex, "$options": "i"}},
            {"location": {"$regex": keyword_regex, "$options": "i"}},
            {"domain_url": {"$regex": keyword_regex, "$options": "i"}},
            {"company_name": {"$regex": keyword_regex, "$options": "i"}},
            {"email_id": {"$regex": keyword_regex, "$options": "i"}},
            {"primary_number": {"$regex": keyword_regex, "$options": "i"}},
        ]

    if name:
        filters.append({"name": {"$regex": normalize_fuzzy_regex_safe(name), "$options": "i"}})

    if title:
        filters.append({"title": {"$regex": normalize_fuzzy_regex_safe(title), "$options": "i"}})

    if company:
        filters.append({"company_name": {"$regex": normalize_fuzzy_regex_safe(company), "$options": "i"}})

    if location:
        filters.append({"location": {"$regex": normalize_fuzzy_regex_safe(location), "$options": "i"}})

    if industry:
        filters.append({"industry": {"$regex": normalize_fuzzy_regex_safe(industry), "$options": "i"}})

    if filters:
        query["$and"] = filters

    return query