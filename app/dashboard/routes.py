from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database.database import get_db
from app.database.models import Company, Contact, Evidence

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    companies = db.scalar(select(func.count()).select_from(Company)) or 0
    contacts = db.scalar(select(func.count()).select_from(Contact)) or 0
    qualified = db.scalar(
        select(func.count()).select_from(Contact).where(Contact.contact_score >= 65)
    ) or 0
    leads = db.scalars(
        select(Contact).order_by(Contact.contact_score.desc()).limit(50)
    ).all()
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "companies": companies,
            "contacts": contacts,
            "qualified": qualified,
            "leads": leads,
        },
    )

@router.get("/leads", response_class=HTMLResponse)
def leads(request: Request, db: Session = Depends(get_db)):
    leads = db.scalars(
        select(Contact).order_by(Contact.contact_score.desc())
    ).all()
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="leads.html",
        context={"leads": leads},
    )
