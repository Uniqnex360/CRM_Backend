from fastapi import FastAPI
from api.user import user_router
from auth.login import auth_router
from api.leads import leads_router
from api.company import company_router
from export.export import export_router
from api.list import list_router
from api.sequence import sequence_router
from api.schedule import schedule_router
from api.email_job import email_router 
from api.sequence_steps import steprouter
from api.web_hooks import webhook_router
from api.step_template import step_template_router
from api.template import template_router
from api.admin import admin_router
from api.migrate import migrate_router

from fastapi_pagination import add_pagination

from fastapi.middleware.cors import CORSMiddleware

from api.step_template import seed_templates

app = FastAPI()


add_pagination(app) 
@app.get("/health")
async def health():
    return {"status": "ok"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","https://crm-frontend-live.vercel.app"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.on_event("startup")
async def startup_event():
    await seed_templates()



app.include_router(admin_router)
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(leads_router)
app.include_router(export_router)
app.include_router(company_router)
app.include_router(list_router)
app.include_router(sequence_router)
app.include_router(schedule_router)
app.include_router(email_router)
app.include_router(steprouter)
app.include_router(step_template_router)
app.include_router(template_router)
app.include_router(webhook_router)
app.include_router(migrate_router)


