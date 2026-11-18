from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.database import SessionLocal, init_db
from app.database.models import Company
from app.scoring.rules import score_evidence


if len(sys.argv) != 2:
    raise SystemExit(
        "Usage: python scripts/score_company.py example.com"
    )


init_db()

domain = sys.argv[1].lower()

db = SessionLocal()

try:
    company = (
        db.query(Company)
        .filter(Company.domain == domain)
        .first()
    )

    if not company:
        raise SystemExit(
            f"Company not found: {domain}"
        )

    texts = [
        evidence.text
        for evidence in company.evidence
        if evidence.text
    ]

    scores = score_evidence(texts)

    company.nz_relevance = scores["nz_relevance"]
    company.au_relevance = scores["au_relevance"]
    company.voice_relevance = scores["voice_relevance"]
    company.company_score = scores["company_score"]

    db.commit()

    print(f"Scored {domain}")
    print(
        f"Company score: {company.company_score} "
        f"(NZ={company.nz_relevance}, "
        f"AU={company.au_relevance}, "
        f"Voice={company.voice_relevance})"
    )

finally:
    db.close()