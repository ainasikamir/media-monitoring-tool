from __future__ import annotations

from pathlib import Path

import psycopg
from psycopg.rows import dict_row

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

    def get_filter_options(self) -> dict[str, list[str]]:
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT DISTINCT outlet FROM articles ORDER BY outlet")
                outlets = [row[0] for row in cur.fetchall()]
                cur.execute("SELECT DISTINCT topic FROM articles ORDER BY topic")
                topics = [row[0] for row in cur.fetchall()]
        return {"outlets": outlets, "topics": topics}

    def list_articles(
        self,
        topic: str | None = None,
        outlet: str | None = None,
        q: str | None = None,
        days: int | None = None,
        limit: int = 100,
    ) -> list[dict]:
        limit = max(1, min(limit, 1000))
        conditions: list[str] = []
        params: list[object] = []

        if topic:
            conditions.append("topic = %s")
            params.append(topic)
        if outlet:
            conditions.append("outlet = %s")
            params.append(outlet)
        if q:
            conditions.append("(article_title ILIKE %s OR article_url ILIKE %s)")
            like = f"%{q}%"
            params.extend([like, like])
        if days is not None:
            days = max(1, min(days, 3650))
            conditions.append("published_at >= NOW() - (%s::int * INTERVAL '1 day')")
            params.append(days)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)

        query = f"""
            SELECT
                article_url,
                article_title,
                author_name,
                topic,
                outlet,
                published_at,
                ingested_at
            FROM articles
            {where_clause}
            ORDER BY published_at DESC NULLS LAST, ingested_at DESC
            LIMIT %s
        """

        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
        return rows
