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
cd /Users/ajnazikamir/media_monitoring_tool
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

2. Configure database URL:

```bash
cp .env.example .env
# edit .env with your Postgres credentials
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

## Database schema
See `media_monitoring/db/schema.sql`.

Main constraints and indexes:
- unique `article_url`
- topic enum-like check constraint
- index on `(topic, published_at desc)`
- index on `(outlet, published_at desc)`

## Next outlets
For your full target list (WSJ, Forbes, NYT, WaPo, Reuters, Bloomberg, Fortune, Wired, Business Insider, TechCrunch, The Verge), add connectors under `media_monitoring/connectors/`.

For paywalled/restricted publishers, use licensed APIs/feeds rather than unrestricted scraping.
