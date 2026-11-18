import re


TITLE_POINTS = {
    "head of voice": 20,
    "voice operations": 20,
    "carrier relations": 20,
    "wholesale": 20,
    "wholesale voice": 20,
    "carrier services": 15,
    "interconnect": 15,
    "voice product": 15,
    "network operations": 10,
    "telecom operations": 10,
    "international carrier": 15,
    "voice network": 15,
    "network architecture": 10,
    "sip": 8,
    "voip": 8,
    "ucaas": 8,
    "cpaas": 8,
}

NEGATIVE_TITLES = {
    "marketing": -20,
    "customer support": -20,
    "recruiter": -15,
}


VOICE_KEYWORDS = [
    "voice",
    "sip",
    "voip",
    "pstn",
    "termination",
    "origination",
    "calling",
    "telephone",
    "telephony",
    "did",
]

# Subset of VOICE_KEYWORDS that specifically signals SIP/VoIP/UCaaS/CPaaS
# technology, as distinct from generic "voice" or "calling" language.
VOICE_TECH_KEYWORDS = [
    "sip",
    "voip",
    "ucaas",
    "cpaas",
]

# Heuristic only: consumer/retail telco language that suggests the site
# is not a wholesale/carrier prospect. Expect to refine this with AI
# classification later rather than growing this list indefinitely.
CONSUMER_KEYWORDS = [
    "prepaid",
    "sim card",
    "mobile plan",
    "family plan",
    "unlimited data",
    "roaming",
]

# Signals that a company already has direct/Tier-1 interconnect and so is
# a weaker broker/intermediary prospect, even if otherwise well-qualified.
# Heuristic only, same caveat as CONSUMER_KEYWORDS above.
DIRECT_INTERCONNECT_KEYWORDS = [
    "direct sip interconnect",
    "direct interconnect",
    "direct connect",
    "tier 1",
    "tier-1",
    "tier1",
    "without aggregators",
]


# Thresholds an evidence relevance score must clear to count as
# "advertises NZ calling" / "advertises AU calling" for scoring purposes.
NZ_AU_ADVERTISED_THRESHOLD = 10

# Thresholds an evidence relevance score must clear to count as
# "SIP/VoIP/UCaaS/CPaaS evidence present".
VOICE_TECH_THRESHOLD = 5


def score_company(
    nz: int,
    au: int,
    voice: int,
    wholesale: bool = False,
    carrier: bool = False,
    international: bool = False,
    consumer_only: bool = False,
    no_voice_evidence: bool = False,
    direct_interconnect: bool = False,
):
    """
    Commercial qualification scoring per the NZ/AU signal table:

      Explicit wholesale voice            +20
      Advertises NZ calling                +15
      Advertises Australia calling         +15
      SIP/VoIP/UCaaS/CPaaS                 +10
      International carrier/interconnect   +15
      Significant international footprint  +10
      Consumer-only / irrelevant           -25
      No evidence of voice traffic         -20
      Established direct/Tier-1 interconnect -15

    nz/au/voice are the existing 0-100 relevance scores from
    score_evidence(); the boolean flags are text-derived signals
    also produced by score_evidence().
    """
    score = 0

    if wholesale:
        score += 20

    if nz >= NZ_AU_ADVERTISED_THRESHOLD:
        score += 15

    if au >= NZ_AU_ADVERTISED_THRESHOLD:
        score += 15

    if voice >= VOICE_TECH_THRESHOLD:
        score += 10

    if carrier:
        score += 15

    if international:
        score += 10

    if consumer_only:
        score -= 25

    if no_voice_evidence:
        score -= 20

    if direct_interconnect:
        score -= 15

    return max(0, min(score, 100))


def classify_score(score: int) -> str:
    """Bucket a company_score per the agreed thresholds."""
    if score >= 80:
        return "priority"
    if score >= 65:
        return "qualified"
    return "hold"


def score_evidence(texts: list[str]) -> dict:
    """
    Calculate company relevance from stored website evidence.

    Returns the individual scoring components as well as
    the final company score.
    """

    combined_text = " ".join(
        text for text in texts if text
    ).lower()

    nz_relevance = 0
    au_relevance = 0
    voice_relevance = 0

    # Geographic relevance
    if "new zealand" in combined_text:
        nz_relevance += 20

    if re.search(r"\bnz\b", combined_text):
        nz_relevance += 10

    if "australia" in combined_text:
        au_relevance += 20

    if re.search(r"\bau\b", combined_text):
        au_relevance += 10

    # Voice / telecommunications relevance
    for keyword in VOICE_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", combined_text):
            voice_relevance += 5

    # Business characteristics
    wholesale = bool(
        re.search(r"\bwholesale\b", combined_text)
    )

    carrier = bool(
        re.search(r"\bcarrier\b", combined_text)
        or re.search(r"\binterconnect\b", combined_text)
    )

    international = bool(
        re.search(r"\binternational\b", combined_text)
    )

    direct_interconnect = any(
        keyword in combined_text for keyword in DIRECT_INTERCONNECT_KEYWORDS
    )

    voice_tech_present = any(
        re.search(rf"\b{re.escape(keyword)}\b", combined_text)
        for keyword in VOICE_TECH_KEYWORDS
    )

    consumer_only = bool(
        combined_text
        and any(keyword in combined_text for keyword in CONSUMER_KEYWORDS)
        and not (wholesale or carrier or voice_tech_present)
    )

    no_voice_evidence = bool(
        combined_text
        and voice_relevance == 0
        and not (wholesale or carrier)
    )

    nz_relevance = min(nz_relevance, 100)
    au_relevance = min(au_relevance, 100)
    voice_relevance = min(voice_relevance, 100)

    company_score = score_company(
        nz_relevance,
        au_relevance,
        voice_relevance,
        wholesale=wholesale,
        carrier=carrier,
        international=international,
        consumer_only=consumer_only,
        no_voice_evidence=no_voice_evidence,
        direct_interconnect=direct_interconnect,
    )

    rationale = []

    if wholesale:
        rationale.append({"signal": "Explicit wholesale voice", "points": 20})
    if nz_relevance >= NZ_AU_ADVERTISED_THRESHOLD:
        rationale.append({"signal": "Advertises NZ calling", "points": 15})
    if au_relevance >= NZ_AU_ADVERTISED_THRESHOLD:
        rationale.append({"signal": "Advertises Australia calling", "points": 15})
    if voice_tech_present:
        rationale.append({"signal": "SIP/VoIP/UCaaS/CPaaS evidence", "points": 10})
    if carrier:
        rationale.append({"signal": "Carrier/interconnect language", "points": 15})
    if international:
        rationale.append({"signal": "International footprint", "points": 10})
    if consumer_only:
        rationale.append({"signal": "Consumer-only / irrelevant", "points": -25})
    if no_voice_evidence:
        rationale.append({"signal": "No evidence of voice traffic", "points": -20})
    if direct_interconnect:
        rationale.append({
            "signal": "Already has direct/Tier-1 interconnect (weaker broker prospect)",
            "points": -15,
        })

    return {
        "nz_relevance": nz_relevance,
        "au_relevance": au_relevance,
        "voice_relevance": voice_relevance,
        "company_score": company_score,
        "score_rationale": rationale,
    }


def score_contact(title: str | None):
    t = (title or "").lower()
    score = 0

    for key, pts in TITLE_POINTS.items():
        if key in t:
            score = max(score, pts)

    for key, pts in NEGATIVE_TITLES.items():
        if key in t:
            score += pts

    return max(0, min(score, 100))


def combined_score(company_score: int, contact_score: int):
    return round(company_score * 0.6 + contact_score * 0.4)


def lead_score(company_score: int, title: str | None) -> int:
    """0-100 lead score: 60% company fit, 40% title fit (title points scaled 20 -> 100)."""
    title_fit = min(100, score_contact(title) * 5)
    return combined_score(company_score, title_fit)