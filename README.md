# NZ/AU Voice Partner Acquisition System - MVP-1

MVP-1 discovers and scores potential NZ/AU wholesale voice partners, enriches contacts, stores evidence in SQLite, and exposes a small FastAPI dashboard.

## What it does

1. Accepts companies/contacts from Apollo or CSV.
2. Crawls company websites for NZ/AU voice relevance.
3. Scores companies and contacts using deterministic rules.
4. Optionally asks an LLM to classify ambiguous leads.
5. Uses Hunter to find/verify business email addresses when configured.
6. Stores evidence, scores and source information in SQLite.
7. Provides a dashboard for reviewing the lead queue.

**MVP-1 deliberately does not automatically send outreach.** Human review comes first.

## Requirements

- Python 3.12+
- Docker Desktop (optional)
- API keys are optional for local CSV/demo operation.
- Apollo and Hunter credentials are required only for those integrations.

## Quick start

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

### Docker

```powershell
docker compose up --build
```

## Load demo data

```powershell
python scripts/load_demo.py
```

Then open http://127.0.0.1:8000/leads

## CSV import

```powershell
python scripts/import_csv.py data/leads.csv
```

CSV columns supported:

- company_name
- domain
- website
- country
- industry
- first_name
- last_name
- job_title
- email
- linkedin_url
- source
- source_url

## Crawl a company

```powershell
python scripts/crawl_company.py example.com
```

## Score all leads

```powershell
python scripts/score_leads.py
```

## Environment

See `.env.example`.

## Project structure

```text
app/
  main.py
  config.py
  database/
    database.py
    models.py
  discovery/
    crawler.py
    apollo.py
  enrichment/
    hunter.py
  scoring/
    rules.py
    ai_score.py
  dashboard/
    routes.py
    templates/
scripts/
tests/
```

## Notes

- Respect applicable laws, provider terms, robots.txt and rate limits.
- Do not treat a public email address as automatic consent for marketing.
- Suppression/consent fields are included in the schema before any outbound automation is added.
