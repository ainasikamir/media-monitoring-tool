from __future__ import annotations

from pathlib import Path

import psycopg

from media_monitoring.models import ArticleRecord


SCHEMA_PATH = Path(__file__).with_name("schema.sql")


class ArticleRepository:
    def __init__(self, dsn: str):
        self.dsn = dsn

    def init_schema(self) -> None:
        with psycopg.connect(self.dsn) as conn:
            conn.execute(SCHEMA_PATH.read_text())
            conn.commit()

    def upsert_articles(self, rows: list[ArticleRecord]) -> int:
        if not rows:
            return 0

        payload = [
            (
                row.outlet,
                row.article_url,
                row.article_title,
                row.author_name,
                row.topic,
                row.published_at,
                row.topic_confidence,
            )
            for row in rows
        ]

        query = """
            INSERT INTO articles (
                outlet,
                article_url,
                article_title,
                author_name,
                topic,
                published_at,
                topic_confidence
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (article_url)
            DO UPDATE SET
                outlet = EXCLUDED.outlet,
                article_title = EXCLUDED.article_title,
                author_name = EXCLUDED.author_name,
                topic = EXCLUDED.topic,
                published_at = EXCLUDED.published_at,
                topic_confidence = EXCLUDED.topic_confidence,
                ingested_at = NOW()
        """

        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.executemany(query, payload)
            conn.commit()

        return len(payload)
