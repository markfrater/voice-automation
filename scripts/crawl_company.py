from datetime import datetime, timezone
import asyncio
import sys
import re
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.database import SessionLocal, init_db
from app.database.models import Company, Evidence
from app.discovery.crawler import crawl_domain
from app.scoring.rules import score_evidence


if len(sys.argv) != 2:
    raise SystemExit("Usage: python scripts/crawl_company.py example.com")


init_db()

domain = sys.argv[1].lower()
results = asyncio.run(crawl_domain(domain))

db = SessionLocal()

company = db.query(Company).filter(Company.domain == domain).first()

if not company:
    company = Company(
        name=domain,
        domain=domain,
        website=f"https://{domain}",
        source="crawler",
    )
    db.add(company)
    db.flush()


# Store or update the evidence collected by the crawler
for result in results:
    evidence = (
        db.query(Evidence)
        .filter(
            Evidence.company_id == company.id,
            Evidence.url == result["url"],
        )
        .first()
    )

    if evidence:
        # Update existing evidence
        evidence.page_title = result["title"]
        evidence.evidence_type = "website"
        evidence.text = result["text"]
        evidence.relevance_score = result["score"]
        evidence.collected_at = datetime.now(timezone.utc)

    else:
        # Create new evidence
        db.add(
            Evidence(
                company_id=company.id,
                url=result["url"],
                page_title=result["title"],
                evidence_type="website",
                text=result["text"],
                relevance_score=result["score"],
            )
        )

# SQLAlchemy should normally include the newly added records after the flush/commit lifecycle, but make this explicit.
db.flush()

# Recalculate company relevance from all stored evidence
scores = score_evidence(
    [
        evidence.text
        for evidence in company.evidence
        if evidence.text
    ]
)

company.nz_relevance = scores["nz_relevance"]
company.au_relevance = scores["au_relevance"]
company.voice_relevance = scores["voice_relevance"]
company.company_score = scores["company_score"]
company.score_rationale = json.dumps(scores["score_rationale"])

db.commit()

company_score = company.company_score
nz_relevance = company.nz_relevance
au_relevance = company.au_relevance
voice_relevance = company.voice_relevance
rationale = scores["score_rationale"]

db.close()

print(f"Stored {len(results)} pages for {domain}.")
print(
    f"Company score: {company_score} "
    f"(NZ={nz_relevance}, "
    f"AU={au_relevance}, "
    f"Voice={voice_relevance})"
)
print("Rationale:")
for item in rationale:
    sign = "+" if item["points"] >= 0 else ""
    print(f"  {sign}{item['points']:>4}  {item['signal']}")