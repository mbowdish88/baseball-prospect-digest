"""Fetch baseball prospect news from Google News RSS feeds."""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone
from time import mktime
from urllib.parse import quote_plus

import feedparser
import requests

import config

logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"


def _article_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def _resolve_url(google_url: str) -> str:
    try:
        resp = requests.head(google_url, allow_redirects=True, timeout=10)
        return resp.url
    except requests.RequestException:
        return google_url


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _parse_entry(entry, seen_ids: set, cutoff: datetime) -> dict | None:
    title = _strip_html(entry.get("title", ""))
    link = entry.get("link", "")
    snippet = _strip_html(entry.get("summary", ""))

    source_info = entry.get("source", {})
    source_name = source_info.get("title", "") if isinstance(source_info, dict) else ""

    published_parsed = entry.get("published_parsed")
    if published_parsed:
        pub_dt = datetime.fromtimestamp(mktime(published_parsed), tz=timezone.utc)
    else:
        pub_dt = None

    if not title or not link:
        return None

    resolved_url = _resolve_url(link)
    aid = _article_id(resolved_url)

    if aid in seen_ids:
        return None
    seen_ids.add(aid)

    if pub_dt and pub_dt < cutoff:
        return None

    return {
        "id": aid,
        "title": title,
        "snippet": snippet,
        "source_name": source_name,
        "pub_date": pub_dt.strftime("%Y-%m-%d") if pub_dt else "",
        "url": resolved_url,
        "source": "news",
    }


def fetch_recent(
    search_terms: list[str] = None,
    max_results: int = None,
    days: int = None,
) -> list[dict]:
    search_terms = search_terms or config.SEARCH_TERMS
    max_results = max_results or config.NEWS_MAX_RESULTS
    days = days or config.LOOKBACK_DAYS

    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days + 1)
    seen_ids: set = set()
    articles: list[dict] = []

    # General prospect search terms
    for term in search_terms:
        url = GOOGLE_NEWS_RSS.format(query=quote_plus(term))
        logger.debug(f"Fetching news RSS for: {term}")
        _fetch_feed(url, articles, seen_ids, cutoff, max_results)
        if len(articles) >= max_results:
            break

    # Site-specific searches
    for site_info in config.SITE_SPECIFIC_SEARCHES:
        site = site_info["site"]
        label = site_info["label"]
        site_terms = site_info.get("terms", [
            "prospect", "top prospects", "draft", "minor league",
        ])

        for term in site_terms:
            query = f"site:{site} {term}"
            url = GOOGLE_NEWS_RSS.format(query=quote_plus(query))
            logger.debug(f"Fetching site-specific news: {label} - {term}")
            _fetch_feed(url, articles, seen_ids, cutoff, max_results * 2)

    logger.info(f"News: retrieved {len(articles)} articles (general + site-specific)")
    return articles


def _fetch_feed(
    url: str,
    articles: list[dict],
    seen_ids: set,
    cutoff: datetime,
    max_total: int,
) -> None:
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        logger.warning(f"Failed to parse RSS feed: {e}")
        return

    for entry in feed.entries:
        parsed = _parse_entry(entry, seen_ids, cutoff)
        if parsed is not None:
            articles.append(parsed)
        if len(articles) >= max_total:
            return
