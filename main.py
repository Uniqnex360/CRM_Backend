from fastapi import FastAPI
from api.user import user_router
from auth.login import auth_router
from api.leads import leads_router
from api.company import company_router
from export.export import export_router
from api.list import list_router


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173/"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(user_router)
app.include_router(auth_router)
app.include_router(leads_router)
app.include_router(export_router)
app.include_router(company_router)
app.include_router(list_router)