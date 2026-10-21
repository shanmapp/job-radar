import os
import time
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_alert(text):
    """Send a plain operational alert (crawler health etc.) via Telegram."""
    status = _post_message({"chat_id": TELEGRAM_CHAT_ID, "text": text,
                            "parse_mode": "Markdown"})
    if status == 400:
        status = _post_message({"chat_id": TELEGRAM_CHAT_ID, "text": text})
    if status != 200:
        # Callers catch and log this; deliberately no URL (it holds the token).
        raise RuntimeError(f"Telegram alert not delivered ({status})")


def _post_message(payload):
    """POST one message, honouring a single 429 retry_after. Returns the status
    code; never raises (a raised HTTPError would print the bot token in its URL)."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    for _ in range(2):
        try:
            r = requests.post(url, data=payload, timeout=20)
        except requests.RequestException as e:
            print(f"Telegram send failed: {type(e).__name__}")
            return None
        if r.status_code != 429:
            return r.status_code
        retry = (r.json().get("parameters") or {}).get("retry_after", 5)
        time.sleep(min(retry, 60) + 1)
    return r.status_code


def send_email(job_details_list, receiverEmail=None):
    # Every job here has already been saved to the DB as "seen", so anything not
    # sent now is lost for good. This used to send only the first 10 per crawl
    # pass and abort the rest on the first failed message — batches of 20-28
    # new brand jobs (Sep–Oct 2026) silently dropped everything past #10.
    for job in job_details_list or []:
        company = job.get("company", "Unknown company")
        title = job.get("title", "Unknown title")
        location = job.get("location", "")
        link = job.get("job_link") or job.get("link") or ""

        body = f"{title}\n{location}" if location else title
        message = f"*{company}*\n{body}"
        if link:
            message += f"\n[View Job]({link})"

        status = _post_message({"chat_id": TELEGRAM_CHAT_ID, "text": message,
                                "parse_mode": "Markdown"})
        if status == 400:
            # Markdown-breaking characters in a title (_ * [ `): resend plain.
            plain = f"{company}\n{body}" + (f"\n{link}" if link else "")
            status = _post_message({"chat_id": TELEGRAM_CHAT_ID, "text": plain})
        if status != 200:
            print(f"Telegram alert not delivered ({status}): {company} - {title}")
        # Telegram allows ~1 message/second to a single chat.
        time.sleep(1.1)

