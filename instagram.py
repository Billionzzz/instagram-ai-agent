import logging
import os

import httpx

GRAPH_API_URL = "https://graph.facebook.com/v21.0"

log = logging.getLogger(__name__)


def send_message(recipient_id: str, text: str) -> None:
    access_token = os.environ["INSTAGRAM_ACCESS_TOKEN"]

    url = f"{GRAPH_API_URL}/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "messaging_type": "RESPONSE",
    }
    params = {"access_token": access_token}

    response = httpx.post(url, json=payload, params=params, timeout=10)

    if response.status_code != 200:
        log.error("Instagram API error %s: %s", response.status_code, response.text)

    response.raise_for_status()
