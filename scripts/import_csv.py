import csv, sys

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.database.database import SessionLocal, init_db
from app.database.models import Company, Contact
from app.scoring.rules import score_contact, combined_score

if len(sys.argv) != 2:
    raise SystemExit("Usage: python scripts/import_csv.py path/to/leads.csv")

init_db()
db = SessionLocal()

with open(sys.argv[1], newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        domain = (row.get("domain") or "").strip().lower()
        company = db.query(Company).filter(Company.domain == domain).first() if domain else None
        if not company:
            company = Company(
                name=row.get("company_name") or "Unknown",
                domain=domain,
                website=row.get("website") or (f"https://{domain}" if domain else None),
                country=row.get("country"),
                industry=row.get("industry"),
                source=row.get("source") or "csv",
                source_url=row.get("source_url"),
            )
            db.add(company)
            db.flush()
        cs = score_contact(row.get("job_title"))
        db.add(Contact(
            company_id=company.id,
            first_name=row.get("first_name"),
            last_name=row.get("last_name"),
            job_title=row.get("job_title"),
            email=row.get("email"),
            linkedin_url=row.get("linkedin_url"),
            contact_score=combined_score(company.company_score, cs),
            email_status="unverified" if row.get("email") else None,
            email_source=row.get("source") or "csv",
        ))

db.commit()
db.close()
print("CSV imported.")
