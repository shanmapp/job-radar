import os
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_email(job_details_list, receiverEmail=None):
    if not job_details_list:
        return

    for job in job_details_list[:10]:
        company = job.get("company", "Unknown company")
        title = job.get("title", "Unknown title")
        location = job.get("location", "")
        link = job.get("job_link") or job.get("link") or ""

        header = f"*{company}*"

        body = f"{title}\n{location}" if location else title

        # Link line
        footer = f"[View Job]({link})" if link else ""

        message = f"{header}\n{body}"
        if footer:
            message += f"\n{footer}"

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
        }

        response = requests.post(url, data=payload, timeout=20)
        response.raise_for_status()

