from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.database import SessionLocal, init_db
from app.database.models import Company


COMPANIES = [
    {
        "name": "iBASIS",
        "domain": "ibasis.com",
        "website": "https://ibasis.com",
        "source_url": "https://ibasis.com/ibasis-acquires-assets-from-telstra/",
    },
    {
        "name": "IDT Global",
        "domain": "idtglobal.com",
        "website": "https://idtglobal.com",
    },
    {
        "name": "DIDWW",
        "domain": "didww.com",
        "website": "https://www.didww.com",
    },
    {
        "name": "Telnyx",
        "domain": "telnyx.com",
        "website": "https://telnyx.com",
    },
    {
        "name": "Bandwidth",
        "domain": "bandwidth.com",
        "website": "https://www.bandwidth.com",
    },
    {
        "name": "didlogic",
        "domain": "didlogic.com",
        "website": "https://didlogic.com",
    },
    {
        "name": "IDT Express",
        "domain": "idtexpress.com",
        "website": "https://www.idtexpress.com",
    },
    {
        "name": "CommPeak",
        "domain": "commpeak.com",
        "website": "https://www.commpeak.com",
    },
    {
        "name": "Symbio Exchange",
        "domain": "symbio.global",
        "website": "https://symbio.global",
    },
    {
        "name": "VoIPcloud",
        "domain": "voipcloud.online",
        "website": "https://www.voipcloud.online",
    },
]


init_db()

db = SessionLocal()

try:
    for item in COMPANIES:

        existing = (
            db.query(Company)
            .filter(Company.domain == item["domain"])
            .first()
        )

        if existing:
            print(f"EXISTS  {item['domain']}")
            continue

        company = Company(
            name=item["name"],
            domain=item["domain"],
           website=item["website"],
           source="web_search",
            source_url=item.get("source_url"),
        )

        db.add(company)
        print(f"ADDED   {item['domain']}")

    db.commit()

finally:
    db.close()