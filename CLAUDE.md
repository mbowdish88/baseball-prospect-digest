# CLAUDE.md

## Project Overview

The Prospect Wire is a baseball prospect digest that collects news daily and publishes a weekly newsletter via Beehiiv. It covers top prospects in college baseball and the MLB minor league system.

## Running the Project

```bash
cd /Users/mbowdish/baseball-prospect-digest
source venv/bin/activate
python main.py
```

Install dependencies: `pip install -r requirements.txt`

The project runs daily at 7 AM Central via GitHub Actions. Manual trigger: `gh workflow run daily-collect.yml`

## Architecture

The pipeline follows: **Daily Collect -> Store -> Weekly Synthesize -> Publish**

### Daily (every day)
1. Fetch prospect news from Google News RSS (general + site-specific searches)
2. Deduplicate against previously seen articles
3. Store new articles in SQLite weekly store

### Weekly (configured publish day, default Sunday)
1. Read all articles from the past 7 days
2. Synthesize into a polished digest via Claude API
3. Publish to Beehiiv
4. Clean up published articles

### Sources (`sources/`)
- `news.py` - Google News RSS with general prospect terms + site-specific searches (MLB.com, Baseball America, FanGraphs, D1Baseball, Perfect Game, Prospects Live)

### Processing (`processing/`)
- `dedup.py` - DedupDB for cross-run deduplication; WeeklyStore for accumulating daily articles
- `summarizer.py` - Claude API generates newsletter HTML with prospect risers/fallers, college spotlight, MiLB standouts, draft watch

### Delivery (`delivery/`)
- `beehiiv.py` - Publishes via Beehiiv API v2

### Configuration (`config.py`)
Central config from `.env`. Defines search terms for MLB prospects, college baseball, draft, and MiLB news.

## Key Design Decisions
- Daily collect + weekly publish pattern (vs. TAVR digest which is daily publish)
- SQLite WeeklyStore accumulates articles across daily runs
- GitHub Actions cache preserves SQLite DBs between runs
- Claude synthesizes across the full week's articles, not just one day
- Same Beehiiv API pattern as tavr-digest project
