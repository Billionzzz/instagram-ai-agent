import json
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request, Response

from agent import get_reply
from instagram import send_message

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="Instagram AI Agent")


@app.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    verify_token = os.environ.get("IG_VERIFY_TOKEN", "")
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        log.info("Webhook verified.")
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification token mismatch.")


@app.post("/webhook")
async def receive_event(request: Request):
    body = await request.body()

    try:
        data = json.loads(body)
    except Exception:
        log.error("Failed to parse JSON body")
        return {"status": "ok"}

    if data.get("object") not in ("instagram", "page"):
        return {"status": "ignored"}

    for entry in data.get("entry", []):
        for messaging in entry.get("messaging", []):
            sender_id = messaging.get("sender", {}).get("id")
            message = messaging.get("message", {})
            text = message.get("text")

            if message.get("is_echo"):
                continue

            if not sender_id or not text:
                continue

            log.info("Message from %s: %s", sender_id, text)

            try:
                reply = get_reply(sender_id, text)
                send_message(sender_id, reply)
                log.info("Replied to %s: %s", sender_id, reply[:80])
            except Exception as exc:
                log.error("Error replying to %s: %s", sender_id, exc, exc_info=True)

    return {"status": "ok"}


@app.get("/")
def health():
    return {"status": "running", "agent": "Instagram AI Agent"}
