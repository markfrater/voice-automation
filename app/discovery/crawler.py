import asyncio
import re
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from app.config import settings

KEYWORDS = {
    "voice": 8, "sip": 8, "voip": 8, "wholesale": 10,
    "termination": 10, "carrier": 10, "interconnect": 10,
    "pstn": 8, "routing": 8, "international voice": 10,
    "australia": 10, "new zealand": 10, "nz": 3, "au": 3,
    "ucaas": 6, "cpaaS": 6, "calling": 5, "did": 5,
}

# Subpages likely to hold country/coverage detail that homepages rarely
# mention (e.g. NZ is a small market for most global carriers). Links
# matching these are crawled before other discovered links.
PRIORITY_PATH_KEYWORDS = [
    "coverage", "countries", "country", "rates", "pricing",
    "network", "destinations", "termination", "products",
]


def _normalize_netloc(netloc: str) -> str:
    """Treat www.example.com and example.com as the same site."""
    return netloc.lower().removeprefix("www.")


def _is_priority_link(url: str) -> bool:
    lowered = url.lower()
    return any(keyword in lowered for keyword in PRIORITY_PATH_KEYWORDS)


async def crawl_domain(domain: str) -> list[dict]:
    domain = domain.strip()
    if not domain.startswith("http"):
        domain = "https://" + domain
    parsed = urlparse(domain)
    base = f"{parsed.scheme}://{parsed.netloc}"
    base_netloc = _normalize_netloc(parsed.netloc)
    queue = [base]
    visited = set()
    results = []
    site_locked = False  # base_netloc gets confirmed/corrected after first fetch

    headers = {"User-Agent": settings.crawler_user_agent}
    timeout = httpx.Timeout(settings.crawler_timeout_seconds)

    async with httpx.AsyncClient(headers=headers, timeout=timeout, follow_redirects=True) as client:
        while queue and len(visited) < settings.crawler_max_pages:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)
            try:
                r = await client.get(url)
                if "text/html" not in r.headers.get("content-type", ""):
                    continue

                # After the first successful fetch, treat wherever we actually
                # landed (post-redirect) as the site's real netloc, so links
                # extracted from this page are compared against the right domain.
                if not site_locked:
                    base_netloc = _normalize_netloc(urlparse(str(r.url)).netloc)
                    site_locked = True

                soup = BeautifulSoup(r.text, "html.parser")
                for tag in soup(["script", "style", "noscript"]):
                    tag.decompose()
                text = " ".join(soup.stripped_strings)
                score, hits = score_text(text)
                results.append({
                    "url": str(r.url),
                    "title": soup.title.get_text(" ", strip=True) if soup.title else "",
                    "text": text[:12000],
                    "score": score,
                    "hits": hits,
                })

                priority_links = []
                normal_links = []
                for a in soup.find_all("a", href=True):
                    href = urljoin(str(r.url), a["href"]).split("#")[0]
                    p = urlparse(href)
                    if _normalize_netloc(p.netloc) != base_netloc or href in visited:
                        continue
                    if _is_priority_link(href):
                        priority_links.append(href)
                    else:
                        normal_links.append(href)

                # Priority links go to the front of the queue so coverage/rates
                # pages get crawled before the max_pages budget is used up on
                # generic marketing pages.
                queue[:0] = priority_links
                queue.extend(normal_links)

                await asyncio.sleep(settings.crawler_delay_seconds)
            except Exception:
                continue
    return results

def score_text(text: str):
    lower = text.lower()
    score = 0
    hits = []
    for keyword, points in KEYWORDS.items():
        count = len(re.findall(re.escape(keyword), lower))
        if count:
            score += min(points * count, points * 2)
            hits.append(keyword)
    return min(score, 100), hits
