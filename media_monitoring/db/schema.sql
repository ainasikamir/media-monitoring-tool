CREATE TABLE IF NOT EXISTS articles (
    id BIGSERIAL PRIMARY KEY,
    outlet TEXT NOT NULL,
    article_url TEXT NOT NULL,
    article_title TEXT NOT NULL,
    author_name TEXT,
    topic TEXT NOT NULL,
    published_at TIMESTAMPTZ,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    topic_confidence NUMERIC(4,3) NOT NULL DEFAULT 0,
    CONSTRAINT uq_articles_article_url UNIQUE (article_url),
    CONSTRAINT chk_topic CHECK (topic IN (
        'ai',
        'business',
        'tech',
        'politics',
        'health',
        'breaking_news',
        'unclassified'
    ))
);

CREATE INDEX IF NOT EXISTS idx_articles_topic_published_at
    ON articles (topic, published_at DESC);

CREATE INDEX IF NOT EXISTS idx_articles_outlet_published_at
    ON articles (outlet, published_at DESC);
