"""Send The Prospect Wire digest via email."""

import logging
import re
import smtplib
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config

logger = logging.getLogger(__name__)


def _html_to_plaintext(html: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html)
    text = re.sub(r"</(p|div|h[1-6]|li|tr)>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def send_digest(digest_html: str, article_count: int) -> None:
    if not config.EMAIL_TO:
        logger.warning("No EMAIL_TO configured. Skipping email send.")
        return

    today = date.today()
    week_start = today - timedelta(days=6)
    subject = (
        f"The Prospect Wire - Week of "
        f"{week_start.strftime('%b %d')} to {today.strftime('%b %d, %Y')} "
        f"({article_count} stories)"
    )

    html_body = digest_html
    text_body = _html_to_plaintext(html_body)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_FROM
    msg["To"] = ", ".join(config.EMAIL_TO)

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    logger.info(f"Connecting to {config.SMTP_HOST}:{config.SMTP_PORT}")

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.sendmail(config.EMAIL_FROM, config.EMAIL_TO, msg.as_string())

    logger.info(f"Digest email sent to {', '.join(config.EMAIL_TO)}")
