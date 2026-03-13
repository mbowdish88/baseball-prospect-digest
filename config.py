import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(exist_ok=True)

load_dotenv(BASE_DIR / ".env", override=True)

# --- Claude API ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

# --- Beehiiv ---
BEEHIIV_API_KEY = os.getenv("BEEHIIV_API_KEY", "")
BEEHIIV_PUB_ID = os.getenv("BEEHIIV_PUB_ID", "")

# --- Agent Settings ---
NEWS_MAX_RESULTS = int(os.getenv("NEWS_MAX_RESULTS", "40"))
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "1"))
PUBLISH_DAY = os.getenv("PUBLISH_DAY", "sunday").lower()  # day of week to publish
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# --- Search Terms: MLB Prospects ---
SEARCH_TERMS_MLB_PROSPECTS = [
    "MLB prospect rankings",
    "MLB top prospects",
    "minor league prospect",
    "MLB Pipeline prospect",
    "Baseball America prospect",
    "MiLB prospect callup",
    "MLB draft prospect",
    "top 100 MLB prospects",
]

SEARCH_TERMS_COLLEGE_BASEBALL = [
    "college baseball prospect",
    "NCAA baseball top prospect",
    "college world series prospect",
    "D1 baseball prospect rankings",
    "college baseball draft prospect",
    "Cape Cod League prospect",
    "college baseball standout",
]

SEARCH_TERMS_DRAFT = [
    "MLB draft rankings",
    "MLB mock draft",
    "MLB draft board",
    "amateur baseball draft",
]

SEARCH_TERMS_MILB = [
    "minor league baseball standout",
    "Triple-A promotion",
    "Double-A prospect",
    "minor league stats leader",
    "MiLB player of the week",
]

SEARCH_TERMS = (
    SEARCH_TERMS_MLB_PROSPECTS
    + SEARCH_TERMS_COLLEGE_BASEBALL
    + SEARCH_TERMS_DRAFT
    + SEARCH_TERMS_MILB
)

# --- Site-Specific News Sources ---
SITE_SPECIFIC_SEARCHES = [
    {"site": "mlb.com", "label": "MLB.com", "terms": [
        "prospect", "top prospects", "draft", "minor league callup",
    ]},
    {"site": "baseballamerica.com", "label": "Baseball America", "terms": [
        "prospect rankings", "top prospects", "draft", "college baseball",
    ]},
    {"site": "fangraphs.com", "label": "FanGraphs", "terms": [
        "prospect", "prospect rankings", "minor league", "draft",
    ]},
    {"site": "prospectslive.com", "label": "Prospects Live"},
    {"site": "d1baseball.com", "label": "D1Baseball", "terms": [
        "prospect", "rankings", "draft", "college world series",
    ]},
    {"site": "perfectgame.org", "label": "Perfect Game", "terms": [
        "prospect", "rankings", "showcase",
    ]},
]

# --- Database ---
DEDUP_DB_PATH = DATA_DIR / "seen_articles.db"
WEEKLY_DB_PATH = DATA_DIR / "weekly_articles.db"
LOG_FILE_PATH = DATA_DIR / "prospect_digest.log"
