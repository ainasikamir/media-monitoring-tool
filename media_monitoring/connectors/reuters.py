from __future__ import annotations

from datetime import datetime
from html import unescape
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from dateutil import parser as dt_parser

from media_monitoring.connectors.base import BaseConnector
from media_monitoring.models import ArticleRecord
from media_monitoring.topics import classify_topic


class ReutersConnector(BaseConnector):
    outlet = "Reuters"
    sitemap_urls = (
        "https://www.reuters.com/arc/outboundfeeds/sitemap/?outputType=xml",
        "https://www.reuters.com/arc/outboundfeeds/sitemap/?outputType=xml&from=100",
        "https://www.reuters.com/arc/outboundfeeds/sitemap/?outputType=xml&from=200",
    )

    def __init__(self, max_items_per_feed: int = 150):
        self.max_items_per_feed = max_items_per_feed

    def _fetch_xml(self, url: str) -> str:
        req = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; MediaMonitoringBot/0.1; +local-dev)",
                "Accept": "application/xml,text/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urlopen(req, timeout=20) as response:
            return response.read().decode("utf-8", errors="replace")

    def _url_to_title(self, article_url: str) -> str:
        path = urlparse(article_url).path.strip("/")
        slug = path.split("/")[-1] if path else ""
        if not slug:
            return ""
        parts = [p for p in slug.split("-") if p and not p.isdigit()]
        if len(parts) >= 3 and all(part.isdigit() for part in parts[-3:]):
            parts = parts[:-3]
        title = " ".join(parts).strip()
        return unescape(title).title()

    def _parse_published(self, raw: str | None) -> datetime | None:
        if not raw:
            return None
        try:
            return dt_parser.parse(raw)
        except (ValueError, TypeError, OverflowError):
            return None

    def fetch(self) -> list[ArticleRecord]:
        records: list[ArticleRecord] = []
        for sitemap_url in self.sitemap_urls:
            if len(records) >= self.max_items_per_feed:
                break
            try:
                xml_payload = self._fetch_xml(sitemap_url)
                root = ET.fromstring(xml_payload)
            except Exception:
                continue

            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            for url_node in root.findall("sm:url", ns):
                if len(records) >= self.max_items_per_feed:
                    break
                loc = url_node.findtext("sm:loc", default="", namespaces=ns).strip()
                lastmod = url_node.findtext("sm:lastmod", default="", namespaces=ns).strip()
                if not loc:
                    continue
                title = self._url_to_title(loc)
                if not title:
                    continue
                classification = classify_topic(title, loc)
                if classification.topic == "unclassified":
                    continue
                records.append(
                    ArticleRecord(
                        outlet=self.outlet,
                        article_url=loc,
                        article_title=title,
                        author_name=None,
                        topic=classification.topic,
                        published_at=self._parse_published(lastmod),
                        topic_confidence=classification.confidence,
                    )
                )
        return records
