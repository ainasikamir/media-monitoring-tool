from __future__ import annotations

from media_monitoring.connectors.rss import RSSConnector


class TheVergeConnector(RSSConnector):
    outlet = "The Verge"
    feed_urls = (
        "https://www.theverge.com/rss/index.xml",
    )
