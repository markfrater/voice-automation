from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.database import SessionLocal, init_db
from app.database.models import Company, Contact, Evidence
from app.scoring.rules import score_company, score_contact, combined_score

init_db()
db = SessionLocal()

demo = [
    {
        "name": "Example Wholesale Voice",
        "domain": "example.com",
        "country": "Australia",
        "industry": "Wholesale Voice",
        "evidence": "Wholesale SIP trunking, international voice termination, Australia and New Zealand calling.",
        "person": ("John", "Smith", "Head of Voice", "john.smith@example.com"),
    },
    {
        "name": "Example UC Provider",
        "domain": "example.net",
        "country": "New Zealand",
        "industry": "UCaaS",
        "evidence": "UCaaS, SIP trunking and business calling services.",
        "person": ("Jane", "Brown", "Carrier Relations Manager", "jane.brown@example.net"),
    },
]

for item in demo:
    company = db.query(Company).filter(Company.domain == item["domain"]).first()

    if company:
        company.name = item["name"]
        company.website = f"https://{item['domain']}"
        company.country = item["country"]
        company.industry = item["industry"]
        company.description = item["evidence"]
        company.nz_relevance = 15
        company.au_relevance = 15
        company.voice_relevance = 20
        company.company_score = score_company(15, 15, 20, wholesale=True, carrier=True, international=True)
    else:
        company = Company(
            name=item["name"], domain=item["domain"], website=f"https://{item['domain']}",
            country=item["country"], industry=item["industry"],
            description=item["evidence"],
            nz_relevance=15, au_relevance=15, voice_relevance=20,
            company_score=score_company(15,15,20,wholesale=True,carrier=True,international=True),
            source="demo", source_url="https://example.com"
        )
        db.add(company)

    db.flush()

    evidence = db.query(Evidence).filter(
        Evidence.company_id == company.id,
        Evidence.url == company.website,
    ).first()

    if evidence:
        evidence.text = item["evidence"]
        evidence.relevance_score = 80
    else:
        db.add(Evidence(company_id=company.id, url=company.website,
                        page_title="Demo evidence", evidence_type="demo",
                        text=item["evidence"], relevance_score=80))

    first, last, title, email = item["person"]
    cs = score_contact(title)
    contact = db.query(Contact).filter(Contact.company_id == company.id, Contact.email == email).first()

    if contact:
        contact.contact_score = combined_score(company.company_score, cs)
    else:
        db.add(Contact(company_id=company.id, first_name=first, last_name=last,
                       job_title=title, email=email, contact_score=combined_score(company.company_score, cs),
                       email_status="demo", email_source="demo"))

db.commit()
db.close()
print("Demo data loaded.")
