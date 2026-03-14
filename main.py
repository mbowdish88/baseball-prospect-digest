#!/usr/bin/env python3
"""The Prospect Wire - weekly baseball prospect digest.

Runs daily to collect news. Publishes a weekly digest on the configured day.
"""

import logging
import sys
import time
from datetime import date

import requests

import config
from sources import news
from processing.dedup import DedupDB, WeeklyStore
from processing.summarizer import create_weekly_digest, build_fallback_digest
from delivery.beehiiv import publish_to_beehiiv
from delivery.emailer import send_digest

# Set up logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("prospect-wire")

DAY_NAMES = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}


def collect_daily():
    """Fetch today's prospect news and store for the weekly digest."""
    logger.info("=== Daily collection starting ===")

    articles = []
    try:
        articles = news.fetch_recent()
        logger.info(f"News: fetched {len(articles)} articles")
    except requests.RequestException as e:
        logger.error(f"News fetch failed: {e}")
    except Exception as e:
        logger.error(f"News unexpected error: {e}", exc_info=True)

    if not articles:
        logger.warning("No articles retrieved. Exiting daily collection.")
        return 0

    # Deduplicate against previously seen articles
    db = DedupDB(config.DEDUP_DB_PATH)
    new_articles = db.filter_new(articles, source="news")

    if not new_articles:
        logger.info("No new articles since last run. Done.")
        return 0

    # Store new articles for the weekly digest
    store = WeeklyStore(config.WEEKLY_DB_PATH)
    store.store_articles(new_articles)

    # Mark as seen for dedup
    db.mark_seen(new_articles)
    db.cleanup(days=90)

    logger.info(f"=== Daily collection complete: {len(new_articles)} new articles stored ===")
    return len(new_articles)


def publish_weekly():
    """Synthesize and publish the weekly digest from stored articles."""
    logger.info("=== Weekly publish starting ===")

    store = WeeklyStore(config.WEEKLY_DB_PATH)
    articles = store.get_week_articles(days=7)

    if not articles:
        logger.warning("No articles collected this week. Skipping publish.")
        return False

    logger.info(f"Synthesizing digest from {len(articles)} articles")

    # Generate digest with Claude (retry once on failure)
    digest_content = None
    for attempt in range(2):
        try:
            digest_content = create_weekly_digest(articles)
            break
        except Exception as e:
            logger.warning(f"Claude API attempt {attempt + 1} failed: {e}")
            if attempt == 0:
                time.sleep(30)

    if digest_content is None:
        logger.error("Claude API unavailable. Using fallback digest.")
        digest_content = build_fallback_digest(articles)

    # Publish to Beehiiv
    try:
        result = publish_to_beehiiv(digest_content, len(articles))
        if result:
            logger.info(f"Beehiiv: published post {result.get('id', 'unknown')}")
    except Exception as e:
        logger.error(f"Beehiiv publish failed: {e}", exc_info=True)

    # Send email copy
    try:
        send_digest(digest_content, len(articles))
    except Exception as e:
        logger.error(f"Email send failed: {e}", exc_info=True)

    # Clean up old articles
    store.clear_published(days=7)

    logger.info("=== Weekly publish complete ===")
    return True


def is_publish_day() -> bool:
    today_weekday = date.today().weekday()
    publish_weekday = DAY_NAMES.get(config.PUBLISH_DAY, 6)  # default sunday
    return today_weekday == publish_weekday


def main():
    # Always collect daily
    collect_daily()

    # Publish only on the configured day
    if is_publish_day():
        logger.info(f"Today is {config.PUBLISH_DAY} — publishing weekly digest")
        publish_weekly()
    else:
        today_name = date.today().strftime("%A").lower()
        logger.info(
            f"Today is {today_name}, publish day is {config.PUBLISH_DAY}. "
            f"Skipping publish."
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    except Exception as e:
        logger.critical(f"Unhandled error: {e}", exc_info=True)
        sys.exit(1)
