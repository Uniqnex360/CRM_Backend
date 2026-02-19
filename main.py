from fastapi import FastAPI
from Api.user import  user_router
from Auth.login import login_router
from Api.leads import leads_router
app = FastAPI()

app.include_router(user_router)
app.include_router(login_router)
app.include_router(leads_router)
