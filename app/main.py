from pathlib import Path
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from app.config import settings
from app.database.database import init_db
from app.dashboard.routes import router
from app.pipeline.leads import router as leads_router

app = FastAPI(title=settings.app_name)
templates = Jinja2Templates(directory=str(Path(__file__).parent / "dashboard" / "templates"))
app.state.templates = templates

@app.on_event("startup")
def startup():
    init_db()

app.include_router(router)
app.include_router(leads_router)
