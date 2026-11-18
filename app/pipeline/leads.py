import asyncio
import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from sqlalchemy import or_

from app.config import settings
from app.database.database import SessionLocal
from app.database.models import (
    Company, Contact, ContactPermission, Evidence, Suppression,
)
from app.discovery.crawler import crawl_domain
from app.scoring.rules import lead_score, score_evidence

router = APIRouter(prefix="/leads", tags=["leads"])
_scoring_lock = asyncio.Lock()

FREE_MAIL = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com",
    "me.com", "live.com", "proton.me", "protonmail.com",
}

# Candidate CSV headers per field, lower-case. First match wins.
# Check "unused_columns" in the import response to see what we ignored.
ALIASES = {
    "first_name": ["first name", "first_name", "firstname"],
    "last_name": ["last name", "last_name", "lastname"],
    "title": ["title", "job title", "job_title"],
    "company": ["company", "company name", "company name for emails", "organization"],
    "email": ["email", "work email", "email address"],
    "email_status": ["email status", "email_status"],
    "website": ["website", "company website", "company domain", "domain"],
    "country": ["country", "company country"],
    "linkedin": ["person linkedin url", "linkedin url", "linkedin"],
    "phone": ["work direct phone", "corporate phone", "mobile phone", "phone"],
}


def _map_headers(fieldnames):
    lowered = {h.strip().lower(): h for h in fieldnames if h}
    mapping = {}
    for field, names in ALIASES.items():
        for name in names:
            if name in lowered:
                mapping[field] = lowered[name]
                break
    return mapping


def _clean_domain(value: str | None) -> str | None:
    if not value:
        return None
    v = value.strip().lower()
    if "//" not in v:
        v = "//" + v
    host = urlparse(v).netloc.split("@")[-1].split(":")[0].removeprefix("www.")
    return host if "." in host else None


def _import_row(db, row, cols, filename, summary):
    def get(field):
        col = cols.get(field)
        return (row.get(col) or "").strip() if col else ""

    email = get("email").lower()
    if not email or "@" not in email:
        summary["skipped_no_email"] += 1
        return

    domain = _clean_domain(get("website")) or _clean_domain(email.split("@", 1)[1])
    if not domain or domain in FREE_MAIL:
        summary["skipped_no_company_domain"] += 1
        return

    if db.query(Suppression).filter(
        or_(Suppression.email == email, Suppression.domain == domain)
    ).first():
        summary["skipped_suppressed"] += 1
        return

    if db.query(Contact).filter(Contact.email == email).first():
        summary["duplicate_contacts"] += 1
        return

    company = db.query(Company).filter(Company.domain == domain).first()
    if not company:
        company = Company(
            name=get("company") or domain,
            domain=domain,
            website=f"https://{domain}",
            country=get("country") or None,
            source="apollo_csv",
            source_url=filename,
        )
        db.add(company)
        db.flush()
        summary["new_companies"] += 1

    contact = Contact(
        company_id=company.id,
        first_name=get("first_name") or None,
        last_name=get("last_name") or None,
        job_title=get("title") or None,
        email=email,
        phone=get("phone") or None,
        linkedin_url=get("linkedin") or None,
        country=get("country") or None,
        email_status=get("email_status") or None,
        email_source="apollo_csv",
    )
    # Company already scored (e.g. seen in an earlier import): score immediately.
    if company.score_rationale is not None:
        contact.contact_score = lead_score(company.company_score, contact.job_title)
    db.add(contact)
    db.flush()

    # Record the source at capture. Consent basis stays "unknown" until we decide
    # per country; we don't assert deemed consent just because Apollo supplied it.
    db.add(ContactPermission(
        contact_id=contact.id,
        country=contact.country,
        source_type="apollo_csv",
        consent_status="unknown",
        last_checked=datetime.now(timezone.utc),
        notes=f"Imported from {filename}",
    ))
    summary["new_contacts"] += 1


@router.post("/import")
def import_leads():
    inbox = Path(settings.leads_inbox_dir)
    processed = Path(settings.leads_processed_dir)
    inbox.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)

    summary = {
        "files": 0, "rows": 0, "new_companies": 0, "new_contacts": 0,
        "duplicate_contacts": 0, "skipped_no_email": 0, "skipped_suppressed": 0,
        "skipped_no_company_domain": 0, "unused_columns": [], "errors": [],
    }
    db = SessionLocal()
    try:
        for path in sorted(inbox.glob("*.csv")):
            with path.open(newline="", encoding="utf-8-sig") as fh:
                reader = csv.DictReader(fh)
                headers = reader.fieldnames or []
                cols = _map_headers(headers)
                if "email" not in cols:
                    summary["errors"].append(f"{path.name}: no email column found")
                    continue
                used = set(cols.values())
                summary["unused_columns"] = sorted({h for h in headers if h and h not in used})
                for row in reader:
                    summary["rows"] += 1
                    _import_row(db, row, cols, path.name, summary)
            db.commit()
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            shutil.move(str(path), str(processed / f"{stamp}_{path.name}"))
            summary["files"] += 1
        return summary
    finally:
        db.close()


def _pending_query(db):
    return db.query(Company).filter(
        Company.source.in_(["apollo_csv", "crawler"]),
        Company.score_rationale.is_(None),
    )


async def _crawl_and_score(db, company):
    pages = await crawl_domain(company.domain)  # returns [] on failure

    if not pages:
        company.company_score = 0
        company.score_rationale = json.dumps(
            [{"signal": "Crawl failed or no pages", "points": 0}]
        )
    else:
        for page in {p["url"]: p for p in pages}.values():
            ev = db.query(Evidence).filter(
                Evidence.company_id == company.id, Evidence.url == page["url"]
            ).first()
            if ev:
                ev.page_title = page["title"]
                ev.text = page["text"]
                ev.relevance_score = page["score"]
                ev.collected_at = datetime.now(timezone.utc)
            else:
                db.add(Evidence(
                    company_id=company.id, url=page["url"], page_title=page["title"],
                    evidence_type="website", text=page["text"],
                    relevance_score=page["score"],
                ))
        db.flush()
        texts = [t for (t,) in db.query(Evidence.text).filter(Evidence.company_id == company.id)]
        scores = score_evidence(texts)
        company.nz_relevance = scores["nz_relevance"]
        company.au_relevance = scores["au_relevance"]
        company.voice_relevance = scores["voice_relevance"]
        company.company_score = scores["company_score"]
        company.score_rationale = json.dumps(scores["score_rationale"])

    for contact in company.contacts:
        contact.contact_score = lead_score(company.company_score, contact.job_title)
    db.commit()
    return {"domain": company.domain, "pages": len(pages), "company_score": company.company_score}


@router.post("/score-pending")
async def score_pending(limit: int = 25):
    if _scoring_lock.locked():
        raise HTTPException(status_code=409, detail="Scoring already running")
    async with _scoring_lock:
        db = SessionLocal()
        try:
            companies = _pending_query(db).order_by(Company.id).limit(limit).all()
            results = [await _crawl_and_score(db, c) for c in companies]
            return {"processed": len(results), "remaining": _pending_query(db).count(), "companies": results}
        finally:
            db.close()


@router.get("/qualified")
def qualified(min_score: int | None = None):
    threshold = settings.outreach_score_threshold if min_score is None else min_score
    db = SessionLocal()
    try:
        rows = (
            db.query(Contact, Company)
            .join(Company, Contact.company_id == Company.id)
            .filter(Contact.contact_score >= threshold, Contact.email.isnot(None))
            .order_by(Contact.contact_score.desc())
            .all()
        )
        return [
            {
                "company": c.name, "domain": c.domain,
                "contact": f"{p.first_name or ''} {p.last_name or ''}".strip(),
                "title": p.job_title, "email": p.email,
                "lead_score": p.contact_score, "company_score": c.company_score,
                "rationale": json.loads(c.score_rationale) if c.score_rationale else [],
            }
            for p, c in rows
        ]
    finally:
        db.close()