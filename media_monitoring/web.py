from __future__ import annotations

import os
from datetime import datetime
from urllib.parse import urlencode

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template_string, request

from media_monitoring.db.repository import ArticleRepository


HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Media Monitoring</title>
  <style>
    :root { color-scheme: light; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; background: #f5f7fb; color: #101828; }
    .wrap { max-width: 1200px; margin: 24px auto; padding: 0 16px; }
    .panel { background: #fff; border: 1px solid #e4e7ec; border-radius: 10px; padding: 16px; margin-bottom: 16px; }
    h1 { margin: 0 0 8px; font-size: 24px; }
    .sub { color: #475467; margin: 0; font-size: 14px; }
    .filters { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }
    label { font-size: 12px; color: #344054; display: block; margin-bottom: 4px; }
    input, select { width: 100%; box-sizing: border-box; padding: 8px; border: 1px solid #d0d5dd; border-radius: 8px; }
    button { margin-top: 8px; padding: 8px 12px; border: 0; border-radius: 8px; background: #175cd3; color: #fff; cursor: pointer; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; background: #fff; }
    th, td { padding: 10px; border-bottom: 1px solid #eaecf0; text-align: left; vertical-align: top; }
    th { background: #f9fafb; position: sticky; top: 0; }
    a { color: #175cd3; text-decoration: none; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; color: #475467; }
    .pager { display: flex; gap: 8px; margin-top: 10px; align-items: center; }
    .pager a { display: inline-block; padding: 6px 10px; border: 1px solid #d0d5dd; border-radius: 8px; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="panel">
      <h1>Media Monitoring Dashboard</h1>
      <p class="sub">Filter ingested articles by topic, outlet, text, and recency.</p>
    </div>

    <form class="panel" method="get" action="/">
      <div class="filters">
        <div>
          <label for="topic">Topic</label>
          <select id="topic" name="topic">
            <option value="">All</option>
            {% for t in topics %}
            <option value="{{t}}" {% if selected_topic==t %}selected{% endif %}>{{t}}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label for="outlet">Outlet</label>
          <select id="outlet" name="outlet">
            <option value="">All</option>
            {% for o in outlets %}
            <option value="{{o}}" {% if selected_outlet==o %}selected{% endif %}>{{o}}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label for="q">Search</label>
          <input id="q" name="q" value="{{q or ''}}" placeholder="title or URL">
        </div>
        <div>
          <label for="days">Days</label>
          <input id="days" type="number" min="1" max="3650" name="days" value="{{days or ''}}" placeholder="e.g. 7">
        </div>
        <div>
          <label for="limit">Limit</label>
          <input id="limit" type="number" min="1" max="1000" name="limit" value="{{limit}}">
        </div>
      </div>
      <button type="submit">Apply Filters</button>
    </form>

    <div class="panel">
      <div class="mono">{{rows|length}} rows on page {{page}}</div>
      <table>
        <thead>
          <tr>
            <th>Published</th>
            <th>Outlet</th>
            <th>Topic</th>
            <th>Title</th>
            <th>Author</th>
          </tr>
        </thead>
        <tbody>
          {% for r in rows %}
          <tr>
            <td>{{r.published_at or ''}}</td>
            <td>{{r.outlet}}</td>
            <td>{{r.topic}}</td>
            <td><a href="{{r.article_url}}" target="_blank" rel="noopener">{{r.article_title}}</a><div class="mono">{{r.article_url}}</div></td>
            <td>{{r.author_name or ''}}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
      <div class="pager">
        {% if prev_url %}
        <a href="{{prev_url}}">Previous</a>
        {% endif %}
        {% if next_url %}
        <a href="{{next_url}}">Next</a>
        {% endif %}
      </div>
    </div>
  </div>
</body>
</html>
"""


def _parse_int(value: str | None, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _to_iso(row: dict) -> dict:
    out = dict(row)
    for key in ("published_at", "ingested_at"):
        value = out.get(key)
        if isinstance(value, datetime):
            out[key] = value.isoformat()
    return out


def create_app() -> Flask:
    load_dotenv()
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL is not set. Create .env from .env.example")

    repo = ArticleRepository(dsn)
    app = Flask(__name__)

    @app.get("/")
    def index():
        options = repo.get_filter_options()
        topic = request.args.get("topic") or None
        outlet = request.args.get("outlet") or None
        q = request.args.get("q") or None
        days_raw = request.args.get("days")
        days = _parse_int(days_raw, default=0)
        days = days if days > 0 else None
        limit = _parse_int(request.args.get("limit"), default=250)
        page = max(1, _parse_int(request.args.get("page"), default=1))
        offset = (page - 1) * limit

        rows = repo.list_articles(
            topic=topic,
            outlet=outlet,
            q=q,
            days=days,
            limit=limit,
            offset=offset,
        )
        rows = [_to_iso(row) for row in rows]

        base_params = {"topic": topic, "outlet": outlet, "q": q, "days": days, "limit": limit}
        base_params = {k: v for k, v in base_params.items() if v is not None and v != ""}
        prev_url = None
        if page > 1:
            prev_params = dict(base_params)
            prev_params["page"] = page - 1
            prev_url = "/?" + urlencode(prev_params)
        next_url = None
        if len(rows) == limit:
            next_params = dict(base_params)
            next_params["page"] = page + 1
            next_url = "/?" + urlencode(next_params)

        return render_template_string(
            HTML_TEMPLATE,
            rows=rows,
            topics=options["topics"],
            outlets=options["outlets"],
            selected_topic=topic,
            selected_outlet=outlet,
            q=q,
            days=days,
            limit=limit,
            page=page,
            prev_url=prev_url,
            next_url=next_url,
        )

    @app.get("/api/articles")
    def api_articles():
        topic = request.args.get("topic") or None
        outlet = request.args.get("outlet") or None
        q = request.args.get("q") or None
        days_raw = request.args.get("days")
        days = _parse_int(days_raw, default=0)
        days = days if days > 0 else None
        limit = _parse_int(request.args.get("limit"), default=100)
        page = max(1, _parse_int(request.args.get("page"), default=1))
        offset = (page - 1) * limit

        rows = repo.list_articles(
            topic=topic,
            outlet=outlet,
            q=q,
            days=days,
            limit=limit,
            offset=offset,
        )
        return jsonify([_to_iso(row) for row in rows])

    @app.get("/health")
    def health():
        return {"ok": True}

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
