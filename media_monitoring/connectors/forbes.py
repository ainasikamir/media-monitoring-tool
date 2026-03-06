from __future__ import annotations

from media_monitoring.connectors.rss import RSSConnector


class ForbesConnector(RSSConnector):
    outlet = "Forbes"
    feed_urls = (
        "https://www.forbes.com/business/feed/",
        "https://www.forbes.com/innovation/feed/",
    )
