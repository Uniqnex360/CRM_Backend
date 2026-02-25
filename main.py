from fastapi import FastAPI
from api.user import  user_router
from auth.login import auth_router
from api.leads import leads_router
from api.company import company_router
from export.export import export_router

app = FastAPI()

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(leads_router)
app.include_router(export_router)
app.include_router(company_router)