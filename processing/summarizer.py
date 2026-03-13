"""Generate weekly baseball prospect digest using Claude API."""

import logging

from anthropic import Anthropic

import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a baseball scout and analyst who produces a weekly newsletter called \
"The Prospect Wire" covering top prospects in college baseball and the MLB \
minor league system. Your audience includes fantasy baseball enthusiasts, \
amateur scouts, college baseball fans, and MLB front-office followers. \
The digest is published on Beehiiv, so it should read like a polished, \
engaging newsletter — authoritative but approachable, with clear narrative flow. \
Think of the tone as a front-office briefing meets a well-written baseball blog."""

DIGEST_PROMPT_TEMPLATE = """\
Produce a weekly baseball prospect newsletter digest from the articles collected \
over the past 7 days below. This will be published directly as "The Prospect Wire" \
on Beehiiv.

## Format Rules (Beehiiv/email compatibility)
- Use ONLY these HTML tags: <h2>, <h3>, <p>, <ul>, <li>, <ol>, <a>, <strong>, \
<em>, <blockquote>, <hr>
- Do NOT use <table>, <div>, <span>, <style>, or any CSS. These are stripped.
- Every section of text should be wrapped in <p> tags.
- Use <hr> between major sections for visual separation.
- Links: <a href="URL">linked text</a>

## Content Instructions
- Begin with an <h2>Weekly Summary</h2> — 3-4 sentences giving the big picture \
of what happened this week in the prospect world. What names are buzzing? \
What trends are emerging?

- Then organize into these sections using <h2> headers (omit sections with no content):
  - Weekly Summary (always include)
  - Prospect Risers — Players whose stock trended up this week. Include stat lines, \
scouting notes, and context for why they're rising.
  - Prospect Fallers — Players whose stock dropped due to injury, poor performance, \
or other factors.
  - College Spotlight — Notable performances from NCAA D1 players projected to be \
drafted. Include stat lines and what scouts are saying.
  - MiLB Standouts — Minor leaguers making a case for promotion. Include recent \
stat lines and organizational context.
  - Transactions & Callups — Relevant roster moves, promotions, demotions, and signings.
  - Draft & Rankings Watch — Updates from major outlets on draft boards or prospect \
rankings changes.
  - Week Ahead — What to watch for next week (upcoming series, showcases, etc.)

- For each player mentioned, try to include: name, team/school, position, age, \
and relevant stats or scouting grades when available.
- Flag any consensus top-100 prospects with <strong>[Top 100]</strong>.
- Note the source of any ranking or scouting report referenced with a link.
- Synthesize across articles — don't just list each article separately. Connect \
the dots and tell the story of the week.
- End with a brief closing thought or look-ahead.
- Tone: expert, concise, analytical but readable as a newsletter. Like a front-office \
briefing — data-driven but with narrative flair.

## Articles Collected This Week ({article_count})
{articles_section}

Produce the newsletter-ready HTML digest now."""


def _format_articles(articles: list[dict]) -> str:
    if not articles:
        return "No articles collected this week."

    parts = []
    for a in articles:
        parts.append(
            f"Title: {a['title']}\n"
            f"Source: {a.get('source_name', 'Unknown')}\n"
            f"Date: {a.get('pub_date', '')}\n"
            f"URL: {a.get('url', '')}\n"
            f"Snippet: {a.get('snippet', '')}\n"
        )
    return "\n---\n".join(parts)


def create_weekly_digest(articles: list[dict]) -> str:
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    prompt = DIGEST_PROMPT_TEMPLATE.format(
        article_count=len(articles),
        articles_section=_format_articles(articles),
    )

    logger.info(
        f"Sending {len(articles)} articles to Claude ({config.CLAUDE_MODEL}) "
        f"for weekly digest"
    )

    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=16384,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    digest_html = message.content[0].text
    logger.info(
        f"Digest generated: {len(digest_html)} chars, "
        f"tokens used: {message.usage.input_tokens} in / {message.usage.output_tokens} out"
    )

    return digest_html


def build_fallback_digest(articles: list[dict]) -> str:
    parts = ["<h2>The Prospect Wire (AI summary unavailable)</h2>"]

    if articles:
        parts.append("<h3>Articles This Week</h3><ul>")
        for a in articles:
            parts.append(
                f'<li><a href="{a.get("url", "#")}">{a.get("title", "Untitled")}</a>'
                f' &mdash; {a.get("source_name", "")}, {a.get("pub_date", "")}</li>'
            )
        parts.append("</ul>")

    return "\n".join(parts)
