import json
import httpx
from app.config import settings

PROMPT = """You are qualifying a B2B wholesale voice prospect.

Determine whether the person plausibly influences selection of voice
termination, carrier, interconnect or routing suppliers for Australia
or New Zealand.

Return ONLY JSON:
{
  "score": 0,
  "relevant": false,
  "reason": "...",
  "buying_role": "...",
  "confidence": 0
}

COMPANY:
{company}

PERSON:
{person}

WEBSITE EVIDENCE:
{evidence}
"""

def classify(company: str, person: str, evidence: str):
    if not settings.openai_api_key:
        return None

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.openai_model,
        "input": PROMPT.format(company=company, person=person, evidence=evidence[:10000]),
    }

    with httpx.Client(timeout=60) as client:
        r = client.post("https://api.openai.com/v1/responses", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()

    text = data.get("output_text", "")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"score": 0, "relevant": False, "reason": text, "buying_role": "", "confidence": 0}
