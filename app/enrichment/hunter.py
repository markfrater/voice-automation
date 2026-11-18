import httpx
from app.config import settings

BASE = "https://api.hunter.io/v2"

def find_email(first_name: str, last_name: str, domain: str):
    if not settings.hunter_api_key:
        raise RuntimeError("HUNTER_API_KEY is not configured")
    params = {
        "first_name": first_name,
        "last_name": last_name,
        "domain": domain,
        "api_key": settings.hunter_api_key,
    }
    with httpx.Client(timeout=30) as client:
        r = client.get(f"{BASE}/email-finder", params=params)
        r.raise_for_status()
        return r.json()

def verify_email(email: str):
    if not settings.hunter_api_key:
        raise RuntimeError("HUNTER_API_KEY is not configured")
    params = {"email": email, "api_key": settings.hunter_api_key}
    with httpx.Client(timeout=30) as client:
        r = client.get(f"{BASE}/email-verifier", params=params)
        r.raise_for_status()
        return r.json()
