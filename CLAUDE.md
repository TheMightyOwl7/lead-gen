# CLAUDE.md — GoogleMapsAPI (Lead Generation Tool)

## What This Is

A lead-generation tool for **Vertere Labs' web design / marketing services**. It finds local
businesses via the Google Places API, then flags the ones worth pitching — primarily businesses
**without a website** (or with a weak one). It layers on website scraping (Firecrawl) and an SEO
audit so a rep can walk into an outreach conversation with concrete "here's what's wrong with your
site" ammunition.

**The core hypothesis for a lead:** a business with good reviews/ratings (a real, established
business) but no website or a poor-quality website = high-value target for a web build.

## Stack

- **Backend:** Python 3.13, FastAPI, SQLAlchemy 2.x, SQLite (`backend/leads.db`)
- **Frontend:** Vanilla HTML/CSS/JS (`frontend/`), served as static files by FastAPI at `/`
- **External APIs:** Google Places API (`googlemaps` SDK), Firecrawl (`firecrawl-py`)
- **HTML parsing:** BeautifulSoup + lxml (SEO analyzer)
- No Docker yet, no deployment config — runs locally via uvicorn.

## Layout

```
backend/
  app/
    main.py           # FastAPI app, CORS, static mount, lifespan (init_db + config validate)
    config.py         # Settings from .env (API keys, monthly limits, DB URL)
    database.py       # SQLAlchemy models + init_db + get_db dependency
    rate_limiter.py   # In-memory per-IP rate limiter (30/min, 10/5s burst)
    routers/
      search.py       # POST /api/search, GET /api/search/usage, /history
      businesses.py   # GET /api/businesses (filters), /{id}, /stats/summary
      research.py     # POST/GET /api/research/{business_id}  (Firecrawl scrape + extract)
      seo.py          # POST /api/seo/analyze/{id}, GET /api/seo/{id}, /issues/{id}
  services/
    places_api.py     # PlacesService — geocode + text search + place details, usage tracking
    firecrawl_api.py  # FirecrawlService — scrape + extract emails/socials/phones/tech
    seo_analyzer.py   # SEOAnalyzer — scores HTML 0-100 across 7 categories
  tests/              # test_api.py, test_lead_scoring.py (pytest)
frontend/
  index.html, css/styles.css, js/api.js, js/app.js
```

## Data Model (SQLite)

- **Search** — one row per search (query, location, radius, results_count)
- **Business** — deduped by Google `place_id`; holds name/address/phone/website/rating/reviews/
  coords. `calculate_lead_score()` lives here (computed, not stored).
- **APIUsage / FirecrawlUsage** — monthly call/credit counters (`YYYY-MM` keyed)
- **CompanyResearch** — Firecrawl scrape output per business (emails, socials, tech, raw markdown)
- **SEOAnalysis** — per-business SEO scores, grade, issues, recommendations

## Lead Scoring (in `database.py` `Business.calculate_lead_score`)

Computed on the fly, max 100:
- No website → **+50** (the hot signal)
- Rating ≥ 4.0 → +20
- Reviews ≥ 100 → +15
- Has phone → +15

## The Workflow (current)

1. `POST /api/search` — geocode location + Places text search, store businesses. Costs ~2 + N
   API calls (1 geocode, 1 search, 1 place-details per result).
2. `GET /api/businesses?has_website=false` — filter to the hot leads.
3. `POST /api/research/{id}` — Firecrawl-scrape a business's site, extract contacts/tech.
4. `POST /api/seo/analyze/{id}` — scrape + score the site's SEO (A+ to F).
5. Review issues via `GET /api/seo/issues/{id}` for the outreach pitch.

Steps 3–5 only work on businesses that **have** a website (needed for the SEO-weakness angle).

## Cost / Budget Guardrails

- Both APIs are metered against monthly limits in `.env` (`MONTHLY_API_LIMIT=500`,
  `FIRECRAWL_MONTHLY_LIMIT=400`). Services check the DB counter before every call and raise
  `APILimitExceeded` / `FirecrawlLimitExceeded` (→ HTTP 429).
- **Follow the global rule:** run enrichment (Firecrawl/SEO) only on *filtered* lead lists, never
  the whole result set. Google enrichment burns budget fast (lessons-learned).
- Place-details lookup (phone/website) costs +1 call *per business* — this is the expensive part
  of a search.

## Conventions & Gotchas

- `datetime.utcnow()` is used throughout — deprecated in 3.12+. Fine for now; migrate to
  `datetime.now(timezone.utc)` when touched.
- `sys.path` is manually patched in `main.py` and `search.py` so `services.*` and `app.*` both
  import — a bit fragile. Run the app from the `backend/` dir (`uvicorn app.main:app --reload`).
- Rate limiter is **in-memory** — resets on restart, not multi-process safe. OK for single local
  instance only.
- README lists "CSV Export" as a feature but there is **no CSV endpoint** in the backend — it's
  either frontend-only or aspirational. Verify before relying on it.
- API keys live in `.env` at the **project root** (not `backend/`). `config.py` walks up two
  parents to find it.

## Running

```bash
cd backend
python -m venv venv && venv\Scripts\activate      # first time
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000  (frontend + API + /docs for Swagger)
```

## Testing

```bash
cd backend && pytest
```
</content>
</invoke>
