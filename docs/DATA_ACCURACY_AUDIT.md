# Data accuracy audit — 2026-08-03

Every figure below was measured against the live Google APIs, not inferred from reading code.
Reproduce any of it with `manage.py gsc_reconcile` / `manage.py ga4_reconcile`.

Site audited: `premierstaff.com` (GSC `sc-domain:premierstaff.com`, GA4 property `318744602`).

---

## How these bugs happen

Four mistakes recur across the codebase. Each one produces a number that looks plausible, which
is why none of them were caught by reading the screen.

1. **Summing a dimension-grouped API response and calling it a total.** Both Google APIs
   withhold or restructure rows when you group by several dimensions. The sum of the parts is
   not the whole, in either direction.
2. **`AVG()` over a ratio.** CTR, position, engagement rate and bounce rate are ratios. An
   unweighted mean over rows lets a 10-impression row count as much as a 10,000-impression one.
3. **Mixing sources within one comparison.** Reading the current period from one table and the
   previous from another turns a difference in completeness into a reported trend.
4. **Fabricated rows that no sync will ever remove.** An upsert only touches keys the API
   returns. Anything written under a key the API never returns is permanent.

---

## Critical

### C1 — 46% of Offsite traffic is design-mockup data

`ga4_traffic_source_daily` holds **22,454 of 48,437 sessions (46%)** under sources GA4 has never
reported for this property:

| source | channel | days present | sessions |
|---|---|---|---|
| forbes.com | Referral | 91 | 5,542 |
| linkedin.com | Social | 91 | 3,049 |
| youtube.com | Video | 91 | 2,891 |
| eventmanagerblog.com | Referral | 91 | 2,850 |
| t.co | Social | 91 | 2,746 |
| yelp.com | Referral | 91 | 2,681 |
| reddit.com | Social | 91 | 2,669 |

Verified for 2026-07-01: GA4 reports 15 rows / 239 sessions; the database holds 23 rows / 524
sessions. Every extra row is one of the above, and GA4 returns none of them.

The uniform "91 days" is the signature — real sources (`google`, `(direct)`, `bing`, `yahoo`)
appear on 93–94 days with uneven totals. These names come from the design prototype's
`Design_features/app/fixtures.js`, which was loaded into the analytics database at some point.

No seeder exists in the current Python code, so nothing regenerates them — but nothing removes
them either. The GA4 upsert only writes keys GA4 returns, so these rows survive every sync.

**Effect:** the Offsite page's sessions, engaged sessions, conversions, revenue, top referrers
and channel mix are roughly half invented.

**Fix:** delete rows whose `(date, channel, source)` GA4 does not return for that date, then
re-sync. Needs a targeted command, not `prune_orphan_site_data` — the `site_id` is correct here;
it is the source that is fake.

### C2 — GA4 sessions are inflated ~58% by the same bug as GSC clicks

Sessions are **not additive across `pagePath`**: one visit to three pages is one session, but
appears as three rows. The connector fetches `(date, country, deviceCategory, pagePath)` and
`seo_daily.sessions` is then summed over it.

Measured, 2026-06-01 → 2026-07-27:

| how GA4 was asked | sessions |
|---|---|
| no dimensions (what the GA4 UI shows) | **13,333** |
| `["date"]` | 13,067 |
| `["date","sessionDefaultChannelGroup","sessionSource"]` | 13,067 |
| `["date","country","deviceCategory","pagePath"]` | **21,077** |
| our `seo_daily` | **21,077** |

Storage is faithful — the wrong question was asked, then summed. Grouping by date alone is
additive and correct, exactly as it was for Search Console.

**Surfaces in:** Overview "top locations by traffic"
([overview_service.py:206](../apps/dashboard/services/overview_service.py#L206)) and Offsite top
landing pages ([offsite_service.py:247](../apps/dashboard/services/offsite_service.py#L247)).

**Fix:** the GA4 equivalent of `seo_daily_totals` — a `dimensions=["date"]` call stored per day,
which headline session counts read. `pageviews` and `conversions` are additive and already close
(96% of GA4); only sessions and users are affected. `totalUsers` is worse still — never additive
at any grain — and is correctly returned as `None` today. It must stay that way until a totals
table exists.

---

## High

### H1 — SEO page by-country and by-device use `AVG()` over ratios

[seo_service.py:68-69, 82](../apps/dashboard/services/seo_service.py#L68) average CTR and
position over every `(date, page)` row in a country.

| country | CTR shown | CTR real | position shown | position real |
|---|---|---|---|---|
| USA | 0.63% | **0.44%** | 34.2 | **31.0** |
| MEX | 3.71% | **2.35%** | 15.7 | **13.6** |
| PHL | 0.71% | **0.30%** | 17.1 | **14.0** |
| IND | 0.30% | **0.20%** | 27.1 | **22.6** |
| GBR | 0.14% | **0.02%** | 40.1 | **45.2** |

CTR is overstated by 40–600%. Same fix already applied to the Overview KPIs: CTR is
`SUM(clicks)/SUM(impressions)`, position is impression-weighted.

### H2 — Offsite engagement rate is an unweighted mean

[offsite_service.py:248](../apps/dashboard/services/offsite_service.py#L248) uses
`AVG(engagement_rate)`. Over 7,370 sessions it shows **77.6%** where the session-weighted figure
is **72.3%**. Engagement rate must be weighted by sessions.

### H3 — GA4 sync is behind

| window | GA4 | our DB |
|---|---|---|
| 24 hours | 99 sessions | **0** |
| 7 days | 1,305 | 388 (29.7%) |

Same situation the GSC sync was in before this week: the connector works, it simply has not run.
Distinct from C2 — this is staleness, that is arithmetic.

---

## Medium

### M1 — `_resolve_site_ids` queries both spellings with `IN`, which double-counts

`ads_service`, `ai_service` and `backlinks_service` each resolve a site to *both* the
`sc-domain:`-prefixed and bare form and query `site_id.in_([both])`. If a connector ever writes
both spellings, every figure on those pages doubles silently.

Currently no table holds both spellings for one site, so **no figure is wrong today** — but this
is the exact mechanism that produced the 123,396 duplicate `premierstaff.com` rows removed on
2026-08-03. The guard belongs at the writer: resolve to the canonical `Site.site_url` before
writing, and drop the two-spelling read.

### M2 — `eventstaff.com` has 113k rows and no `Site` row

47,851 `seo_daily` + 65,437 `keyword_rankings` + 950 `pages` + 262 `backlinks` under a key no
page reads. Left in place deliberately — it may be a competitor site removed from `sites` rather
than junk. `manage.py prune_orphan_site_data --apply --only eventstaff.com` when confirmed.

### M3 — cross-keyword position averages are unweighted

`shared_queries` and `keywords_service` average `KeywordRanking.position` across keywords.
Averaging one keyword's position across *dates* is a fair time-average and is fine. Averaging
*across keywords* gives every keyword equal weight regardless of traffic, which is not how
Search Console defines average position. Defensible for a rank-tracker view; it should not be
compared against the Overview's figure, which is impression-weighted, and the two will differ.

---

## Checked and found correct

- **Hardcoded zeros are documented honest empties**, not fabrications — `ads_service` `conv_value`
  (no revenue column exists), `ai_service` per-keyword mentions, `keywords_service` `monthly` /
  `serpFeatures`, `sync_api_service` `est_cost`. Each carries a comment naming what is missing.
- **`backlinks`** — no mockup contamination; 362 real rows.
- **`totalUsers`** — never summed anywhere; returned as `None`.
- **`ga4_traffic_source_daily` has no duplicate rows** — the unique constraint holds. Its
  inflation is C1 (fake sources), not double-writing.
- **`anomaly_service`'s `AVG()` calls** are averages of daily values used as an anomaly baseline.
  That is the correct use of a mean.
- **Search Console figures after this week's work** — 7d / 28d / 90d clicks, impressions, CTR and
  position all tie out exactly to the Search Console UI.

---

## Suggested order

1. **C1** — delete the mockup sources. Nearly half the Offsite page is fiction; nothing else on
   that page can be trusted until they are gone.
2. **C2** — `ga4_daily_totals`, mirroring `seo_daily_totals`.
3. **H1, H2** — ratio arithmetic. Small, self-contained, fully testable.
4. **H3** — run the GA4 sync; confirm with `ga4_reconcile`.
5. **M1** — canonicalise `site_id` at the writer and drop the two-spelling read.
6. **M2** — decide on `eventstaff.com`.
