import os
import httpx

GRAPH_API_URL = "https://graph.facebook.com/v21.0"


def send_message(recipient_id: str, text: str) -> None:
    """Send a text message to an Instagram user via the Messenger API."""
    access_token = os.environ["INSTAGRAM_ACCESS_TOKEN"]

    url = f"{GRAPH_API_URL}/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
    }
    params = {"access_token": access_token}

    response = httpx.post(url, json=payload, params=params, timeout=10)
    response.raise_for_status()
