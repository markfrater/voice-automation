from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.database import SessionLocal, init_db
from app.database.models import Company, Contact
from app.scoring.rules import score_company, score_contact, combined_score

init_db()
db = SessionLocal()

companies = db.query(Company).all()
for c in companies:
    # Basic heuristic from stored description/evidence.
    text = (c.description or "").lower()
    c.nz_relevance = 20 if ("new zealand" in text or "nz" in text) else c.nz_relevance
    c.au_relevance = 20 if ("australia" in text or "au" in text) else c.au_relevance
    c.voice_relevance = max(c.voice_relevance, 20 if any(k in text for k in ["voice", "sip", "voip", "termination"]) else 0)
    c.company_score = score_company(
        c.nz_relevance, c.au_relevance, c.voice_relevance,
        wholesale="wholesale" in text,
        carrier="carrier" in text or "interconnect" in text,
        international="international" in text,
    )

for p in db.query(Contact).all():
    p.contact_score = combined_score(c.company_score if (c := p.company) else 0, score_contact(p.job_title))

db.commit()
db.close()
print("Scores updated.")
