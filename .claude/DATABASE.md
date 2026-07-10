# FuseHealth — Database Reference

**Phase 3 status:** Production schema complete. Real data migrated.

**Migration counts (2026-06-11, `python manage.py migrate_legacy_data`):**
`sites: 1` · `seo_daily: 5596` · `keyword_rankings: 1223` · `pages: 51` ·
`competitor_domains: 26` · `indexing_status: 51` · `seo_aggregates: 118` ·
`ai_summaries: 1` · `insights: 5` · (ads/backlinks/competitors 0 — credentials not available)

---

## 1. Two-Database Boundary

| | `django_internal.db` | `fusehealth.db` |
|---|---|---|
| **Managed by** | Django ORM + migrations | SQLAlchemy — `pipeline/db/schema.py` → `init_db()` |
| **Owns** | App/operational state | Analytics + intelligence data |
| **Written by** | Django views, `apps.sync` engine | Pipeline connectors, analytics/prediction services |
| **Read by** | Django views, HTMX polling | Dashboard page views |
| **Created** | `manage.py migrate` | `init_db(get_engine(settings.ANALYTICS_DB_PATH))` |

**Cross-DB join key:** `site_url` — a plain string (e.g. `sc-domain:fusehealth.com`) shared between
Django `CharField` fields and SQLAlchemy `site_id` columns. No cross-DB foreign keys.

**Tables re-homed from old MVP:**

| Old MVP table | New home | Reason |
|---|---|---|
| `sync_log` | Django `sync.SyncLog` | Sync state; HTMX reads it from Django's DB |
| `refresh_jobs` | Django `sync.RefreshRun` | Live progress bar; Django writes it |
| `insights` | Django `dashboard.Insight` | User-entered with a User FK; app state |
| `users` | Django `auth.User` + `accounts.UserProfile` | Replaced by Phase 2 |
| all analytics | stay in `fusehealth.db` (refined) | Pipeline reads/writes them via SQLAlchemy |

---

## 2. Django Operational Models (`django_internal.db`)

### 2.1 `sync.SyncLog` — per-connector last status

One row per `(connector, site_url)`. Updated by the sync engine after each connector run.

| Field | Type | Notes |
|---|---|---|
| `connector` | CharField(100), indexed | connector key e.g. `gsc`, `dataforseo_keywords` |
| `site_url` | CharField(255), indexed | cross-DB key = `sites.site_url` |
| `status` | CharField(20) | `never` \| `running` \| `success` \| `error` (`SyncStatus` choices) |
| `last_synced` | DateTimeField(null) | when it last finished |
| `records_written` | IntegerField(default=0) | |
| `error_message` | TextField(null) | |
| `duration_seconds` | FloatField(null) | |

**Unique:** `(connector, site_url)`.

### 2.2 `sync.RefreshRun` — live per-run progress

One row per user-triggered refresh. The HTMX progress bar polls this ~every 2s.

| Field | Type | Notes |
|---|---|---|
| `site_url` | CharField(255) | |
| `scope` | CharField(50) | `all` or page key (`seo`, `keywords`, …) |
| `triggered_by` | FK(User, null, SET_NULL) | |
| `status` | CharField(20), indexed | `running` \| `success` \| `error` (`RefreshStatus` choices) |
| `current_connector` | CharField(100, null) | what's running right now |
| `completed_count` | IntegerField(default=0) | |
| `total_count` | IntegerField(default=0) | denominator for the % bar |
| `records_written` | IntegerField(default=0) | |
| `error_message` | TextField(null) | |
| `started_at` | DateTimeField(auto_now_add), indexed | |
| `finished_at` | DateTimeField(null) | |

**Property:** `percent` → `int(100 * completed_count / total_count)` (0 when total=0).
**Default ordering:** `-started_at`.

### 2.3 `dashboard.Insight` — team-entered event context

Qualitative notes linking business events to metrics. User-editable via admin/forms.

| Field | Type | Notes |
|---|---|---|
| `site_url` | CharField(255), indexed | |
| `date` | DateField, indexed | event date |
| `team` | CharField(50) | `seo` \| `ads` \| `product` \| `marketing` |
| `title` | CharField(200) | |
| `description` | TextField | |
| `affected_metric` | CharField(100, null) | `clicks`, `ctr`, `spend`, … |
| `dimension` | CharField(200, null) | e.g. `keyword:telehealth`, `page:/blog` |
| `impact` | CharField(50) | `positive` \| `negative` \| `neutral` |
| `hypothesis` | TextField(null) | |
| `action_taken` | TextField(null) | |
| `created_by` | FK(User, null, SET_NULL) | |
| `is_verified` | BooleanField(default=False) | |
| `created_at` | DateTimeField(auto_now_add) | |

**Default ordering:** `-date`.

---

## 3. Analytics Schema (`fusehealth.db` — SQLAlchemy)

> **Global invariants:**
> - No `data_source` columns anywhere (demo data purged; contract forbids fake data).
> - `site_id` columns hold the site's URL string (`Site.site_url`), NOT an integer FK.
> - CTR and ROAS are stored but also derivable from raw components at read time.

### 3.1 `sites` — tracked domain registry

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `site_url` | String(255) NOT NULL UNIQUE | the cross-DB join key |
| `site_name` | String(255) null | display name |
| `slug` | String(100) null, unique, indexed | URL-safe project identifier for the SPA/API (e.g. `GET /api/projects` routing) |
| `vertical` | String(255) null | industry/vertical label, e.g. `telehealth` — shown in Settings |
| `location` | String(255) null, default=`"United States"` | primary market/location for keyword & competitor research |
| `gsc_property` | String(255) null | e.g. `sc-domain:fusehealth.com` |
| `ga4_property_id` | String(100) null | numeric GA4 property ID |
| `dataforseo_target_domain` | String(255) null | bare domain for DataForSEO |
| `is_active` | Integer default=1, indexed | |
| `created_at` | DateTime server_default=now | |

**Fed by:** manual / `.env` backfill during setup.

**`slug`/`vertical`/`location` (Phase A):** added to `pipeline/db/schema.py`'s `Site` class and
backfilled via `python manage.py add_project_fields` — an idempotent one-off command, not a
Django migration (this table lives in the SQLAlchemy-managed `fusehealth.db`, not
`django_internal.db`, so Django's migration system doesn't cover it). Run it once on any
pre-existing database.

### 3.2 `seo_daily` — daily GSC + GA4 metrics

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `date` | Date NOT NULL, indexed | |
| `site_id` | String(255) NOT NULL, indexed | |
| `clicks` | Integer default=0 | GSC |
| `impressions` | Integer default=0 | GSC |
| `ctr` | Float default=0.0 | GSC (also derivable: clicks/impressions) |
| `avg_position` | Float default=0.0 | GSC |
| `sessions` | Integer default=0 | GA4 |
| `pageviews` | Integer default=0 | GA4 |
| `bounce_rate` | Float default=0.0 | GA4 |
| `conversions` | Integer default=0 | GA4 |
| `users` | Integer default=0 | GA4 |
| `new_users` | Integer default=0 | GA4 |
| `engagement_rate` | Float default=0.0 | GA4 |
| `country` | String(100) null, indexed | GSC dimension |
| `device` | String(50) null, indexed | GSC dimension |
| `landing_page` | Text null, indexed | GSC dimension |

**Upsert key:** `(date, site_id, country, device, landing_page)`.
**Composite index:** `(site_id, date)`.
**Caveat:** NULL-dimension rows (aggregate, no breakdown) are treated as DISTINCT by SQLite's unique index — migration is safe as one-time only.

### 3.3 `keyword_rankings` — daily keyword positions

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `date` | Date NOT NULL, indexed | |
| `site_id` | String(255) NOT NULL, indexed | |
| `keyword` | String(500) NOT NULL, indexed | |
| `position` | Integer null | DataForSEO SERP position |
| `url` | Text null | ranking URL |
| `clicks` | Integer null | GSC |
| `impressions` | Integer null | GSC |
| `ctr` | Float null | GSC |
| `search_volume` | Integer null | DataForSEO |
| `keyword_difficulty` | Float null | DataForSEO |
| `cpc` | Float null | DataForSEO |
| `intent` | String(100) null, indexed | DataForSEO |
| `trend` | Text null | DataForSEO (JSON array) |

**Upsert key:** `(date, site_id, keyword)`. **Composite index:** `(site_id, date)`.

### 3.4 `pages` — page inventory

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `site_id` | String(255) NOT NULL, indexed | |
| `url` | Text NOT NULL, indexed | |
| `cms_type` | String(50) null | `webflow` \| `wordpress` \| `framer` |
| `title` | Text null | |
| `sessions` | Integer default=0 | GA4 |
| `clicks` | Integer default=0 | GSC |
| `impressions` | Integer default=0 | GSC |
| `issues` | Text null | JSON list from DataForSEO On-Page |
| `author` | String(200) null, indexed | CMS |
| `meta_title` | Text null | CMS |
| `meta_description` | Text null | CMS |
| `publish_date` | Date null, indexed | CMS |
| `last_modified` | Date null | CMS |
| `last_updated` | DateTime onupdate=now | |

**Upsert key:** `(site_id, url)`.

### 3.5 `ad_metrics_daily` — paid-ad metrics

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `date` | Date NOT NULL, indexed | |
| `site_id` | String(255) NOT NULL, indexed | |
| `platform` | String(50) NOT NULL, indexed | `google` \| `meta` \| `linkedin` |
| `campaign` | String(500) null | |
| `campaign_id` | String(100) null | |
| `spend` | Float default=0.0 | |
| `clicks` | Integer default=0 | |
| `impressions` | Integer default=0 | |
| `conversions` | Integer default=0 | |
| `roas` | Float null | also derivable: revenue/spend |

**Upsert key:** `(date, site_id, platform, campaign)`. **Composite index:** `(site_id, date)`.

### 3.6 `backlinks` — inbound link inventory

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `site_id` | String(255) NOT NULL, indexed | |
| `referring_domain` | String(500) NOT NULL, indexed | DataForSEO Backlinks |
| `target_url` | Text NOT NULL | |
| `anchor` | Text null | |
| `status` | String(20) default=`live` | |
| `dofollow` | Integer default=1 | |
| `domain_rank` | Integer null | |
| `first_seen` | Date null | |
| `last_seen` | Date null | |

**Upsert key:** `(site_id, referring_domain, target_url)`.

### 3.7 `competitor_visibility` — share-of-voice over time

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `date` | Date NOT NULL, indexed | |
| `site_id` | String(255) NOT NULL, indexed | |
| `competitor_domain` | String(255) NOT NULL, indexed | |
| `visibility_pct` | Float null | DataForSEO Competitors |
| `shared_keywords` | Integer default=0 | |

**Upsert key:** `(date, site_id, competitor_domain)`.

### 3.8 `competitor_domains` — auto-discovered competitors

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `site_id` | String(255) NOT NULL, indexed | |
| `competitor_domain` | String(255) NOT NULL, indexed | DataForSEO Labs |
| `intersections` | Integer default=0 | shared keywords count |
| `full_domain_metrics_organic_count` | Integer default=0 | |
| `avg_position` | Float null | |
| `median_position` | Float null | |
| `etv` | Float null | estimated traffic value |
| `last_fetched` | DateTime server_default=now | |

**Upsert key:** `(site_id, competitor_domain)`.

### 3.9 `technical_issues` — on-page SEO issues

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `site_id` | String(255) NOT NULL, indexed | |
| `url` | Text NOT NULL, indexed | DataForSEO On-Page |
| `issue_type` | String(200) NOT NULL | |
| `severity` | String(20) null | |
| `description` | Text null | |
| `detected_at` | DateTime server_default=now | |

**Upsert key:** `(site_id, url, issue_type)` — fixes the old schema that blind-appended (duplicated issues on every re-sync).

### 3.10 `page_speed` — Core Web Vitals + Lighthouse scores

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `site_id` | String(255) NOT NULL, indexed | |
| `url` | Text NOT NULL, indexed | PageSpeed Insights |
| `strategy` | String(20) NOT NULL | `mobile` \| `desktop` |
| `performance_score` | Integer null | 0–100 |
| `seo_score` | Integer null | 0–100 |
| `accessibility_score` | Integer null | 0–100 |
| `best_practices_score` | Integer null | 0–100 |
| `lcp_ms` | Float null | Largest Contentful Paint |
| `cls` | Float null | Cumulative Layout Shift |
| `inp_ms` | Float null | Interaction to Next Paint |
| `fcp_ms` | Float null | First Contentful Paint |
| `ttfb_ms` | Float null | Time to First Byte |
| `si_ms` | Float null | Speed Index |
| `last_checked` | DateTime server_default=now | |

**Upsert key:** `(site_id, url, strategy)`.

### 3.11 `indexing_status` — Google URL Inspection results

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `site_id` | String(255) NOT NULL, indexed | |
| `url` | Text NOT NULL, indexed | URL Inspection API |
| `verdict` | String(20) null | `PASS` \| `FAIL` \| `NEUTRAL` |
| `coverage_state` | String(100) null | |
| `indexing_state` | String(50) null | |
| `last_crawl_time` | DateTime null | |
| `crawl_status` | String(50) null | |
| `robots_txt_state` | String(50) null | |
| `mobile_usability` | String(20) null | |
| `rich_results_status` | String(50) null | |
| `last_checked` | DateTime server_default=now | |

**Upsert key:** `(site_id, url)`.

### 3.12 `seo_aggregates` — pre-rolled period totals

Built by `aggregate_service`. Avoids expensive GROUP BY on every page load.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `site_id` | String(255) NOT NULL, indexed | |
| `period_type` | String(10) NOT NULL, indexed | `daily` \| `weekly` \| `monthly` \| `rolling_28` |
| `period_start` | Date NOT NULL, indexed | |
| `period_end` | Date NOT NULL | |
| `clicks` | Integer default=0 | |
| `impressions` | Integer default=0 | |
| `ctr` | Float default=0.0 | |
| `avg_position` | Float default=0.0 | |
| `sessions` | Integer default=0 | |
| `pageviews` | Integer default=0 | |
| `users` | Integer default=0 | |
| `new_users` | Integer default=0 | |
| `returning_users` | Integer default=0 | |
| `engagement_rate` | Float default=0.0 | |
| `rebuilt_at` | DateTime server_default=now | |

**Upsert key:** `(site_id, period_type, period_start)`.

### 3.13 `ai_summaries` — weekly AI intelligence

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `week_start` | Date NOT NULL, indexed | |
| `site_id` | String(255) NOT NULL, indexed | |
| `summary_text` | Text null | OpenAI generated |
| `generated_at` | DateTime server_default=now | |
| `model_used` | String(100) null | e.g. `gpt-4o` |
| `period_start` | Date null | |
| `period_end` | Date null | |

**Upsert key:** `(week_start, site_id)`.

### 3.14 `anomalies` — detected metric anomalies (reactive)

What already changed. Complements `risk_signals` (what's coming).

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `date` | Date NOT NULL, indexed | |
| `site_id` | String(255) NOT NULL, indexed | **NEW in Phase 3** (was global) |
| `metric_type` | String(50) NOT NULL, indexed | `seo_clicks` \| `sessions` \| … |
| `actual_value` | Float NOT NULL | |
| `baseline_value` | Float NOT NULL | |
| `deviation_pct` | Float NOT NULL | (actual − baseline) / baseline × 100 |
| `severity` | String(20) NOT NULL | `low` \| `medium` \| `high` |
| `description` | Text null | |
| `is_acknowledged` | Integer default=0 | |
| `detected_at` | DateTime server_default=now, indexed | |

**Upsert key:** `(date, site_id, metric_type)`.

### 3.15 `comparative_metrics` — WoW / MoM comparisons

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `site_id` | String(255) NOT NULL, indexed | **NEW in Phase 3** |
| `metric_type` | String(50) NOT NULL, indexed | |
| `week_start` | Date NOT NULL, indexed | |
| `current_week_value` | Float NOT NULL | |
| `previous_week_value` | Float NOT NULL | |
| `wow_change_pct` | Float null | |
| `mom_change_pct` | Float null | |
| `four_week_avg` | Float null | |
| `twelve_week_avg` | Float null | |
| `trend_direction` | String(20) null | `up` \| `down` \| `stable` |
| `data_freshness` | DateTime server_default=now | |

**Upsert key:** `(site_id, metric_type, week_start)`.

---

## 4. Prediction & Intelligence Layer (`fusehealth.db`)

These tables are not filled by any external API. A future prediction service reads the
raw/aggregate tables, computes, and writes here.

### 4.1 `metric_forecasts` — numeric forward projections

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `site_id` | String(255) NOT NULL, indexed | |
| `metric_type` | String(50) NOT NULL | `clicks` \| `impressions` \| `sessions` \| `avg_position` \| … |
| `period_type` | String(10) NOT NULL | `daily` \| `weekly` \| `monthly` |
| `target_date` | Date NOT NULL | the future period being predicted |
| `predicted_value` | Float NOT NULL | |
| `lower_bound` | Float null | confidence interval low |
| `upper_bound` | Float null | confidence interval high |
| `model_name` | String(100) NOT NULL | e.g. `holt_winters`, `linear_trend` |
| `model_version` | String(50) null | |
| `actual_value` | Float null | backfilled when target_date arrives |
| `error_pct` | Float null | \|actual − predicted\| / actual, backfilled |
| `generated_at` | DateTime server_default=now | |

**Upsert key:** `(site_id, metric_type, period_type, target_date, model_name)`.
**Index:** `(site_id, metric_type, target_date)`.

### 4.2 `keyword_opportunities` — scored "what to target next"

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `site_id` | String(255) NOT NULL, indexed | |
| `keyword` | String(500) NOT NULL | |
| `current_position` | Integer null | null = not yet ranking |
| `search_volume` | Integer null | |
| `keyword_difficulty` | Float null | |
| `cpc` | Float null | |
| `opportunity_score` | Float NOT NULL default=0.0 | 0–100 composite |
| `opportunity_type` | String(50) null | `quick_win` \| `striking_distance` \| `content_gap` \| `rising` |
| `estimated_traffic_gain` | Float null | projected extra clicks if captured |
| `rationale` | Text null | human-readable "why" |
| `computed_at` | DateTime server_default=now | |

**Upsert key:** `(site_id, keyword)` — upsert latest snapshot.
**Index:** `(site_id, opportunity_score)`.

### 4.3 `risk_signals` — proactive entity-level warnings

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `site_id` | String(255) NOT NULL, indexed | |
| `signal_type` | String(50) NOT NULL | `ranking_drop_risk` \| `traffic_decline` \| `indexing_risk` \| `opportunity` |
| `entity_type` | String(20) NOT NULL | `page` \| `keyword` \| `site` |
| `entity_ref` | Text NOT NULL | URL or keyword |
| `severity` | String(20) null | `low` \| `medium` \| `high` |
| `confidence` | Float null | 0–1 |
| `predicted_impact` | Text null | e.g. "−40% clicks within 30d" |
| `rationale` | Text null | |
| `status` | String(20) default=`open`, indexed | `open` \| `acknowledged` \| `resolved` |
| `detected_at` | DateTime server_default=now | |
| `expires_at` | Date null | when the prediction window closes |

**Indexes:** `(site_id, status)`, `signal_type`.

---

## 5. Page → Table Read Map

| Page | Reads from |
|---|---|
| Overview | `seo_aggregates`, `keyword_rankings`, `ad_metrics_daily`, `ai_summaries`, `risk_signals`, `anomalies` |
| SEO | `seo_daily`, `seo_aggregates`, `comparative_metrics` |
| Ads | `ad_metrics_daily` |
| Keywords | `keyword_rankings`, `keyword_opportunities` |
| Pages / Indexing | `pages`, `indexing_status`, `page_speed`, `technical_issues` |
| Backlinks | `backlinks` |
| Team Insights | `dashboard.Insight` (Django), `anomalies` |
| Alerts | `anomalies`, `risk_signals` |
| Settings | `sites`, `sync.SyncLog` (Django) |
| Positioning | `competitor_domains`, `competitor_visibility`, `keyword_rankings`, `metric_forecasts` |

---

## 6. Migration Command

`python manage.py migrate_legacy_data [--source path/to/cache.db]`

Copies real data from the Streamlit MVP DB into the new databases:
1. Analytics rows → `fusehealth.db` via SQLite `ATTACH DATABASE` + `INSERT OR IGNORE … SELECT WHERE data_source = 'real'`.
2. Insights → Django `dashboard.Insight` via `get_or_create` (idempotent).
3. Backfills `site_id` on `anomalies` / `comparative_metrics` from the active site.
4. Prints before/after row counts per table.

Default source: `../data/cache.db` (parent directory of `fusehealth/`).

---

## 7. Schema Files

| File | Purpose |
|---|---|
| `pipeline/db/schema.py` | SQLAlchemy table definitions (`Base`, all 18 table classes, `init_db()`) |
| `pipeline/db/engine.py` | `get_engine(db_path)` and `get_sessionmaker(db_path)` factories |
| `apps/sync/models.py` | Django `SyncLog`, `RefreshRun` |
| `apps/dashboard/models.py` | Django `Insight` |
| `apps/sync/management/commands/migrate_legacy_data.py` | one-time migration command |
