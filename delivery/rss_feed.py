"""Generate an RSS feed XML file for Beehiiv RSS-to-Send integration."""

import logging
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

logger = logging.getLogger(__name__)

FEED_DIR = Path(__file__).resolve().parent.parent / "docs"
FEED_FILE = FEED_DIR / "feed.xml"
SITE_URL = ""  # Set after GitHub Pages is enabled


def _get_site_url() -> str:
    """Derive the GitHub Pages URL from git remote."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, check=True,
        )
        remote = result.stdout.strip()
        # https://github.com/user/repo.git -> https://user.github.io/repo
        if "github.com" in remote:
            parts = remote.replace(".git", "").split("github.com")[-1].strip("/").split("/")
            if len(parts) == 2:
                return f"https://{parts[0]}.github.io/{parts[1]}"
    except Exception:
        pass
    return "https://mbowdish88.github.io/baseball-prospect-digest"


def publish_to_rss(digest_html: str, article_count: int) -> str:
    """Write the digest as an RSS feed item. Returns the feed file path."""
    FEED_DIR.mkdir(exist_ok=True)

    site_url = _get_site_url()
    today = date.today()
    week_start = today - timedelta(days=6)
    title = (
        f"The Prospect Wire - Week of "
        f"{week_start.strftime('%b %d')} to {today.strftime('%b %d, %Y')}"
    )
    pub_date = format_datetime(datetime.now(timezone.utc))
    guid = f"{site_url}/digest-{today.isoformat()}"

    # Build RSS XML
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "The Prospect Wire"
    ET.SubElement(channel, "link").text = site_url
    ET.SubElement(channel, "description").text = (
        "A weekly scouting report on top prospects in college baseball "
        "and the MLB minor leagues."
    )
    ET.SubElement(channel, "language").text = "en-us"
    ET.SubElement(channel, "lastBuildDate").text = pub_date

    # Load existing items to preserve history
    existing_items = []
    if FEED_FILE.exists():
        try:
            old_tree = ET.parse(FEED_FILE)
            old_channel = old_tree.find(".//channel")
            if old_channel is not None:
                existing_items = old_channel.findall("item")
        except ET.ParseError:
            logger.warning("Could not parse existing feed.xml, starting fresh")

    # Add new item
    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, "link").text = guid
    ET.SubElement(item, "guid").text = guid
    ET.SubElement(item, "pubDate").text = pub_date
    ET.SubElement(item, "description").text = digest_html

    # Re-add previous items (keep last 12 weeks)
    for old_item in existing_items[:11]:
        channel.append(old_item)

    # Write feed
    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    tree.write(FEED_FILE, encoding="unicode", xml_declaration=True)

    logger.info(f"RSS feed written to {FEED_FILE}")
    return str(FEED_FILE)
