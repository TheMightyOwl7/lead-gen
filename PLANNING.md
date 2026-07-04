# Planning — GoogleMapsAPI (Lead Generation Tool)

Improvement roadmap for turning this from a manual, one-business-at-a-time tool into an
automated lead-outreach engine. Ordered by leverage.

---

## Where it stands

Solid bones: clean service/router separation, both APIs budget-metered, lead scoring + SEO
scoring already work. But it's currently a **manual, one-business-at-a-time tool**. The real
value — and the automation — lives in the gap between "search returned 20 businesses" and
"here are 5 ranked leads with a pitch ready."

---

## 1. Fix the lead-model contradiction (do first)

The core thesis is *"no website = hot lead"* (+50 points). But the SEO audit and Firecrawl
research **only run on businesses that HAVE a website** (`research.py:42`, `seo.py:37` both 400
if no site). So the two enrichment tools can't touch the hottest leads.

There are really **two distinct lead types**, and the tool should model both:

- **No website** → sell a new build. Signal = strong rating + reviews + phone. *No enrichment
  needed.*
- **Weak website** → sell a redesign/SEO. Signal = has a site but low SEO grade (D/F), old tech
  (Wix/Squarespace / no HTTPS / not mobile).

Lead scoring currently ignores SEO grade entirely. **Fold the SEO score into the lead score**
for the second group — a business with an A+ site is a *bad* redesign lead even with great
reviews.

## 2. Automate the pipeline (the big one)

Today a rep does: search → eyeball list → POST research per ID → POST seo per ID → read issues.
That's 4 manual steps × N businesses. Replace with **one endpoint**:

`POST /api/campaigns` → `{query, location, radius, filters}` that:

1. Searches Places
2. Auto-filters to leads worth enriching (respecting budget)
3. Fans out research + SEO **concurrently** (everything is synchronous today — a 20-business run
   blocks for minutes)
4. Ranks by combined lead score
5. Returns a ranked, pitch-ready list

Needs **background jobs**. FastAPI `BackgroundTasks` is the zero-dependency start; a lightweight
queue if it grows. Add a `Campaign` table + status polling so the frontend shows progress.

## 3. Tools worth adding

| Tool | Why | Cost |
|---|---|---|
| **Google PageSpeed Insights API** | Real Core Web Vitals / performance score — far more persuasive than HTML heuristics. | Free |
| **Direct domain probe** (cross-check "no website") | Google frequently lacks the website field even when one exists; a cheap `httpx` HEAD to `businessname.com` guesses catches false positives. | Free |
| **LLM pitch generation (Claude)** | Turn SEO issues + business context into a personalized outreach email/opener automatically. Highest-value automation for outreach volume. Use `claude-haiku-4-5` for cost. | Cheap |
| **Email verification** (MX check, stdlib) | Emails are already regex-scraped in `firecrawl_api.py` — validate before they hit a CRM. | Free |
| **Push leads to MercLeads** | The CRM already exists. This tool should *feed* it, not be a dead end. | — |

**Reduce Firecrawl dependency** for basic scraping — for simple HTML, use `httpx` (already a
dependency) + BeautifulSoup and save Firecrawl credits for JS-heavy sites only. Firecrawl's
400/mo free limit is the tightest constraint.

## 4. Smaller fixes noticed

- **CSV export is in the README but not in the backend** — no endpoint exists. Build it or fix
  the README.
- **Rate limiter is in-memory** — fine locally, breaks on multi-process/deploy.
- **`datetime.utcnow()`** deprecated throughout — migrate to `datetime.now(timezone.utc)` when
  touched.
- **No dedup across searches into lead lists**, and no "already contacted" state — the same
  businesses will re-surface. If this feeds a CRM, contacted-state belongs there.
- **SEO analyzer weighting bug**: docstring says title=20/meta=20 but `analyze()` weights title
  0.10 + meta 0.10 (`seo_analyzer.py:69-70`) — inconsistent with the documented breakdown. The
  grade is slightly off from spec.

---

## Recommended phasing

1. **Unify the lead model** (§1) + fold SEO grade into scoring — small, high-impact, unblocks
   everything.
2. **Build the one-shot campaign endpoint with concurrent enrichment + background jobs** (§2) —
   the core automation.
3. **Add PageSpeed + Claude-generated pitches + MercLeads handoff** (§3) — turns it from a lead
   *finder* into a lead *outreach engine*.

**Start point:** Phase 1 is the cheapest change with the biggest downstream payoff and a clean
place to see the pattern before committing to the async campaign work.
</content>
