from fastapi_pagination import Params
from fastapi import Query

class CustomParams(Params):
    size: int = Query(20, ge=1, le=20)
    sort_by: str = "name"
    sort_order: str = "asc"