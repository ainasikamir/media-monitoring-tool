from __future__ import annotations

from media_monitoring.connectors.rss import RSSConnector


class TechCrunchConnector(RSSConnector):
    outlet = "TechCrunch"
    feed_urls = (
        "https://techcrunch.com/feed/",
    )
