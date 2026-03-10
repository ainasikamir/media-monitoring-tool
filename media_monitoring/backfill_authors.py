from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv

from media_monitoring.connectors.byline import extract_author_from_url
from media_monitoring.db.repository import ArticleRepository


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill missing author names")
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Max rows with missing authors to scan",
    )
    return parser.parse_args()


def run() -> None:
    load_dotenv()
    args = parse_args()

    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL is not set. Create .env from .env.example")

    repo = ArticleRepository(dsn)
    targets = repo.list_missing_authors(limit=args.limit)

    updated = 0
    scanned = 0
    fallback_updates = 0
    for row in targets:
        scanned += 1
        url = row["article_url"]
        outlet = row["outlet"]
        author = extract_author_from_url(url)
        if not author and outlet == "Reuters":
            author = "Reuters Staff"
            fallback_updates += 1
        if not author:
            continue
        repo.update_author(url, author)
        updated += 1

    print("Author backfill complete")
    print(f"- scanned={scanned}")
    print(f"- updated={updated}")
    print(f"- fallback_reuters_staff={fallback_updates}")


if __name__ == "__main__":
    run()
