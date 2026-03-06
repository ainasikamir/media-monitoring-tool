from __future__ import annotations

import argparse
import os
from collections import defaultdict

from dotenv import load_dotenv

from media_monitoring.connectors.business_insider import BusinessInsiderConnector
from media_monitoring.connectors.forbes import ForbesConnector
from media_monitoring.connectors.fortune import FortuneConnector
from media_monitoring.connectors.reuters import ReutersConnector
from media_monitoring.connectors.techcrunch import TechCrunchConnector
from media_monitoring.connectors.the_verge import TheVergeConnector
from media_monitoring.connectors.wired import WiredConnector
from media_monitoring.db.repository import ArticleRepository
from media_monitoring.models import ArticleRecord


CONNECTOR_REGISTRY = {
    "business_insider": BusinessInsiderConnector,
    "forbes": ForbesConnector,
    "fortune": FortuneConnector,
    "reuters": ReutersConnector,
    "techcrunch": TechCrunchConnector,
    "the_verge": TheVergeConnector,
    "wired": WiredConnector,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run media monitoring ingestion")
    parser.add_argument(
        "--sources",
        nargs="*",
        default=list(CONNECTOR_REGISTRY.keys()),
        choices=list(CONNECTOR_REGISTRY.keys()),
        help="Subset of sources to ingest",
    )
    parser.add_argument(
        "--max-items-per-feed",
        type=int,
        default=150,
        help="Max entries per RSS feed",
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Create database schema before ingestion",
    )
    return parser.parse_args()


def dedupe_by_url(records: list[ArticleRecord]) -> list[ArticleRecord]:
    by_url: dict[str, ArticleRecord] = {}
    for record in records:
        by_url[record.article_url] = record
    return list(by_url.values())


def run() -> None:
    load_dotenv()
    args = parse_args()

    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL is not set. Create .env from .env.example")

    repo = ArticleRepository(dsn)
    if args.init_db:
        repo.init_schema()

    fetched: list[ArticleRecord] = []
    source_counts: dict[str, int] = defaultdict(int)

    for source_key in args.sources:
        connector = CONNECTOR_REGISTRY[source_key](max_items_per_feed=args.max_items_per_feed)
        rows = connector.fetch()
        fetched.extend(rows)
        source_counts[source_key] = len(rows)

    deduped = dedupe_by_url(fetched)
    inserted = repo.upsert_articles(deduped)

    print("Ingestion complete")
    for source_key in args.sources:
        print(f"- {source_key}: fetched={source_counts[source_key]}")
    print(f"- deduped_total={len(deduped)}")
    print(f"- upserted={inserted}")


if __name__ == "__main__":
    run()
