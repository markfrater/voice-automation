import httpx
from app.config import settings

APOLLO_URL = "https://api.apollo.io/api/v1/mixed_people/api_search"

DEFAULT_TITLES = [
    "Head of Voice", "Voice Operations", "Carrier Relations",
    "Wholesale", "Wholesale Voice", "Carrier Services",
    "Interconnect", "Voice Product", "Network Operations",
    "Telecom Operations", "International Carrier", "Voice Network",
    "SIP", "VoIP", "UCaaS", "CPaaS", "Network Architecture"
]

def search_people(titles=None, page=1, per_page=25):
    if not settings.apollo_api_key:
        raise RuntimeError("APOLLO_API_KEY is not configured")
    titles = titles or DEFAULT_TITLES
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "x-api-key": settings.apollo_api_key,
    }
    payload = {
        "person_titles": titles,
        "page": page,
        "per_page": per_page,
    }
    with httpx.Client(timeout=30) as client:
        r = client.post(APOLLO_URL, headers=headers, json=payload)
        r.raise_for_status()
        return r.json()
