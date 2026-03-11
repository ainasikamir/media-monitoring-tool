# Media Monitoring Tool (MVP)

Topic-focused monitoring for selected outlets, starting with:
- Business Insider
- Forbes
- Fortune
- Reuters
- TechCrunch
- The Verge
- Wired

This MVP ingests article metadata into Postgres with these core fields:
- `article_url`
- `article_title`
- `author_name`
- `topic`

It also stores operational fields: `outlet`, `published_at`, `ingested_at`, `topic_confidence`.

## Topics
Supported topic labels:
- `sxsw`
- `ai`
- `business`
- `tech`
- `politics`
- `health`
- `breaking_news`
- `unclassified`

The ingestion path filters out `unclassified` records for cleaner monitoring feeds.

## Setup
1. Create a virtual environment and install dependencies:

```bash
cd media_monitoring_tool
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

2. Configure database URL:

```bash
cp .env.example .env
# edit .env with your Postgres credentials
```

Optional: enable Oxylabs proxy (used by default when configured):

```bash
OXYLABS_USERNAME=...
OXYLABS_PASSWORD=...
OXYLABS_PROXY_HOST=pr.oxylabs.io
OXYLABS_PROXY_PORT=7777
USE_PROXY_DEFAULT=true
```

3. Run ingestion and initialize schema:

```bash
python -m media_monitoring.ingest --init-db
```

4. Run ingestion (without schema init):

```bash
python -m media_monitoring.ingest
```

5. Ingest only one source:

```bash
python -m media_monitoring.ingest --sources reuters
```

To improve author coverage when feeds omit bylines:

```bash
python -m media_monitoring.ingest --max-author-lookups 80
```

Backfill missing authors in already-saved rows:

```bash
python -m media_monitoring.backfill_authors --limit 300
```

Note: Reuters article pages currently block non-browser scraping in this workflow.
When Reuters bylines cannot be extracted, `author_name` may remain blank.

## Web UI + API
Run a local dashboard and JSON API:

```bash
python -m media_monitoring.web
```

Then open:
- `http://127.0.0.1:8000/` (UI)
- `http://127.0.0.1:8000/api/articles` (JSON)

Supported query params for UI/API:
- `topic` (e.g. `ai`)
- `outlet` (e.g. `Reuters`)
- `q` (search title/url text)
- `days` (e.g. `7`)
- `limit` (max `1000`)
- `page` (pagination page number)

Set title branding (optional):

```bash
export APP_TITLE="Annie's Press Tracker"
```

## Database schema
See `media_monitoring/db/schema.sql`.

Main constraints and indexes:
- unique `article_url`
- topic enum-like check constraint
- index on `(topic, published_at desc)`
- index on `(outlet, published_at desc)`

## Public Deployment (Free)
To share with others, deploy instead of using `127.0.0.1`.

Suggested stack:
- App hosting: Render (free web service)
- Database: Neon Postgres (free tier)

### 1) Create a free Postgres database (Neon)
1. Create a Neon project and copy the connection string.
2. In Neon SQL editor, run the schema from `media_monitoring/db/schema.sql`.

### 2) Deploy app on Render
1. New Web Service -> connect this GitHub repo.
2. Use name/slug: `annies-press-tracker`.
3. Build command:

```bash
pip install -e .
```

4. Start command:

```bash
gunicorn -w 2 -k gthread -b 0.0.0.0:$PORT media_monitoring.web:app
```

5. Environment variables:
- `DATABASE_URL` = your Neon connection string
- `APP_TITLE` = `Annie's Press Tracker`

After deploy, share the Render URL, e.g.:
- `https://annies-press-tracker.onrender.com`

### Blueprint option (faster)
This repo includes `render.yaml` for one-step setup:
1. In Render, click **New +** -> **Blueprint**.
2. Select this GitHub repo.
3. Set `DATABASE_URL` when prompted (for both services).
4. Deploy.

### 3) Keep data fresh daily
`render.yaml` already defines a daily cron ingestion job.

Current cron schedule is `0 17 * * *` (UTC), which is:
- 10:00 AM in Pacific Standard Time
- 9:00 AM in Pacific Daylight Time

If you want exactly 10:00 AM year-round, change schedule seasonally between:
- `0 17 * * *` (standard time)
- `0 18 * * *` (daylight time)
