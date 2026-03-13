"""SQLite-backed deduplication and weekly article storage."""

import json
import logging
import sqlite3
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DedupDB:
    def __init__(self, db_path: str):
        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS seen_articles (
                    article_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    title TEXT,
                    url TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_source ON seen_articles(source)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_first_seen ON seen_articles(first_seen)"
            )

    def filter_new(self, articles: list[dict], source: str) -> list[dict]:
        if not articles:
            return []

        with sqlite3.connect(self.db_path) as conn:
            ids = [a["id"] for a in articles]
            placeholders = ",".join("?" for _ in ids)
            cursor = conn.execute(
                f"SELECT article_id FROM seen_articles WHERE article_id IN ({placeholders})",
                ids,
            )
            seen_ids = {row[0] for row in cursor.fetchall()}

        new_articles = [a for a in articles if a["id"] not in seen_ids]
        logger.info(f"{source}: {len(new_articles)} new out of {len(articles)} total")
        return new_articles

    def mark_seen(self, articles: list[dict]):
        if not articles:
            return

        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                """
                INSERT OR IGNORE INTO seen_articles (article_id, source, title, url)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (a["id"], a.get("source", "unknown"), a.get("title", ""), a.get("url", ""))
                    for a in articles
                ],
            )
        logger.info(f"Marked {len(articles)} articles as seen")

    def cleanup(self, days: int = 90):
        cutoff = datetime.now() - timedelta(days=days)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM seen_articles WHERE first_seen < ?",
                (cutoff.isoformat(),),
            )
            if cursor.rowcount > 0:
                logger.info(f"Cleaned up {cursor.rowcount} articles older than {days} days")


class WeeklyStore:
    """Stores daily collected articles for weekly aggregation."""

    def __init__(self, db_path: str):
        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS weekly_articles (
                    article_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    title TEXT,
                    url TEXT,
                    snippet TEXT,
                    source_name TEXT,
                    pub_date TEXT,
                    collected_date DATE DEFAULT (date('now')),
                    article_json TEXT
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_collected ON weekly_articles(collected_date)"
            )

    def store_articles(self, articles: list[dict]):
        if not articles:
            return

        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                """
                INSERT OR IGNORE INTO weekly_articles
                    (article_id, source, title, url, snippet, source_name, pub_date, article_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        a["id"], a.get("source", "unknown"), a.get("title", ""),
                        a.get("url", ""), a.get("snippet", ""),
                        a.get("source_name", ""), a.get("pub_date", ""),
                        json.dumps(a),
                    )
                    for a in articles
                ],
            )
        logger.info(f"Stored {len(articles)} articles for weekly digest")

    def get_week_articles(self, days: int = 7) -> list[dict]:
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT article_json FROM weekly_articles WHERE collected_date >= ?",
                (cutoff,),
            )
            articles = [json.loads(row[0]) for row in cursor.fetchall()]
        logger.info(f"Retrieved {len(articles)} articles from past {days} days")
        return articles

    def clear_published(self, days: int = 7):
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM weekly_articles WHERE collected_date < ?",
                (cutoff,),
            )
            if cursor.rowcount > 0:
                logger.info(f"Cleared {cursor.rowcount} published articles")
