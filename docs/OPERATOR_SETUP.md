# Operator setup — what you do

Everything here needs *your* machine, *your* credentials, or *your* Google account. None of it
can be done from inside the codebase.

Do them in this order. Steps 1–3 are the ones that matter; 4–6 can wait.

---

## Step 0 — Back up first (5 minutes, do not skip)

You are about to copy two live databases. Copy them somewhere safe before you start.

```bash
cd "f:/Vash Studios/FuseHealth/Limitless_marketing_dashboard"
mkdir backup_2026_07_27
cp django_internal.db  backup_2026_07_27/
cp data/fusehealth.db  backup_2026_07_27/
```

The migration itself opens both files **read-only** (`file:...?mode=ro`, SQLite refuses writes
at the driver level), so it cannot damage them. The backup is insurance against everything else.

---

## Step 1 — Install the dependencies

```bash
pip install -r requirements.txt
```

This brings in `psycopg[binary]>=3.2`, the Postgres driver. Until it is installed, **nothing
Postgres-related has ever actually run** — the Postgres code paths were written and
syntax-checked, but never executed against a real server.

Check it worked:

```bash
python -c "import psycopg; print(psycopg.__version__)"
```

---

## Step 2 — Move to PostgreSQL

You said you already set Postgres up locally. Good — this is the part that makes it live.

### 2a. Create the database

One database holds **both** sets of tables (Django's and the analytics pipeline's). Their names
don't collide, so this is deliberate, not a shortcut.

```bash
createdb fusehealth
```

### 2b. Fill in `.env`

`POSTGRES_DB` is the **master switch**:

| `POSTGRES_DB` | What happens |
|---|---|
| **empty** | SQLite, exactly as today. This is your rollback path. |
| **filled** | Django *and* the analytics pipeline both point at Postgres. |

```ini
POSTGRES_DB=fusehealth
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

The password is URL-encoded when the connection string is built, so `@`, `#`, `:` etc. are safe.

### 2c. Create the Django tables

```bash
python manage.py migrate
```

### 2d. Dry run — this writes nothing at all

```bash
python manage.py migrate_to_postgres --dry-run
```

Read the output. It prints a row count per table. **If anything looks wrong, stop here** — you
have changed nothing yet.

### 2e. The real run

```bash
python manage.py migrate_to_postgres
```

Every insert is `ON CONFLICT DO NOTHING`, so re-running it cannot duplicate rows. It prints row
counts before and after each table and **exits non-zero if the numbers don't justify success** —
so a silent partial migration is not possible. If it exits non-zero, send me the output.

### 2f. Check it

```bash
python manage.py runserver
```

Open the dashboard. Your data should be there. If anything is wrong: **blank `POSTGRES_DB` in
`.env` and restart** — you are instantly back on SQLite with your data untouched.

---

## Step 3 — Turn on the automatic weekly sync

The scheduler exists and works, but it needs Windows to call it. Until you do this, cadences are
saved and the Settings panel is honest about what *would* run — but nothing fires.

### 3a. Check what it would do

```bash
python manage.py run_scheduled_syncs --dry-run
```

Prints which modules are due, and starts nothing.

### 3b. Register the hourly task

Open **Task Scheduler** → *Create Task* (not "Basic Task"):

- **General** → *Run whether user is logged on or not*
- **Triggers** → *New* → Daily, *Repeat task every 1 hour* for *Indefinitely*
- **Actions** → *New* → Start a program:
  - **Program:** the full path to your `python.exe`
  - **Arguments:** `manage.py run_scheduled_syncs`
  - **Start in:** `f:\Vash Studios\FuseHealth\Limitless_marketing_dashboard`

Hourly is correct — the command decides *itself* what is actually due from each module's cadence
and its real run history. Running it hourly does not mean syncing hourly.

### 3c. Confirm

Settings → Automation shows the next run date. That date comes from the *same* logic the command
acts on, so what it promises and what happens cannot drift apart.

---

## Step 4 — Google Ads (only if you want Ads data)

Search Terms and Attribution are **fully built and wired**. They are empty for one reason: a new
developer token is issued at **Basic Access**, which returns report data for test accounts only.
Against a real account it authenticates fine and hands back an empty report.

1. Apply for **Standard Access**: <https://developers.google.com/google-ads/api/docs/access-levels>
2. Approval usually takes a few business days.
3. Once approved, fill in `.env`:
   ```ini
   GOOGLE_ADS_DEVELOPER_TOKEN=
   GOOGLE_ADS_CUSTOMER_ID=            # digits only, dashes are stripped
   GOOGLE_ADS_LOGIN_CUSTOMER_ID=      # only if under a manager (MCC) account
   ```
   `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REFRESH_TOKEN` are shared with Search
   Console — already set if GSC syncs.
4. **Restart the server.** `.env` is read once at import; editing it on a running process does
   nothing.
5. Settings → Connections → Google Ads → **Run Ads sync now**.

⚠️ **"Refresh all" does not run the Ads connectors.** Only the `ads` scope does — that button,
or the Ads pages' own refresh. This is deliberate, not a bug.

---

## Step 5 — Sentry (optional)

Leave `SENTRY_DSN` blank and nothing is initialised — the dependency is never even imported.

```ini
SENTRY_DSN=https://...@sentry.io/...
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.0
```

`send_default_pii=False` is already set, so user data is not sent.

---

## Step 6 — Look at it in a browser

I have verified data shapes, database writes and that every JS bundle parses. **I have not seen a
rendered page.** Worth your eyes on:

- **Overview** → "Slowest pages" (was permanently empty until a missing-import fix; should now
  show data) and the two new sections, Top keywords and Positioning vs Competitors
- **Site Audit** → Statistics. Numbers should be stated over *measured* pages only (roughly 48 of
  154 on your data), not all of them. TBT reads `—` until a sync stores a real value.
- **Settings → Usage & Budget** → real 90-day spend. The monthly figure carries a `PROJECTED`
  chip; that is deliberate — it is a forecast sitting next to measurements.
- **Settings → Alerts & Rules** → two rules now, not four. `pos_drop` and `lost_backlink` were
  removed because nothing read them.
- **Position Tracking** → keyword volumes. A keyword tracked since the last sync now reads `—`
  instead of triggering a paid API call on page load.

---

## If something breaks

**Postgres:** blank `POSTGRES_DB` in `.env`, restart. You are on SQLite again immediately; the
migration never wrote to the SQLite files.

**Scheduler:** disable the Task Scheduler entry. Refresh buttons still work by hand.

**Anything else:** `git diff` shows every change; nothing is committed yet.
