import json
import logging
import os
import urllib.parse

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from agent import get_reply
from instagram import send_message

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="Instagram AI Agent")

APP_ID = "1414145400476681"
BASE_URL = "https://instagram-ai-agent-production-96f3.up.railway.app"
CALLBACK_URL = f"{BASE_URL}/auth/callback"


# ---------------------------------------------------------------------------
# OAuth setup — visit /setup to get your Page Access Token automatically
# ---------------------------------------------------------------------------
@app.get("/setup")
def setup():
    scope = "pages_messaging,instagram_manage_messages,pages_show_list,pages_read_engagement,pages_manage_metadata"
    params = urllib.parse.urlencode({
        "client_id": APP_ID,
        "redirect_uri": CALLBACK_URL,
        "scope": scope,
        "response_type": "code",
    })
    oauth_url = f"https://www.facebook.com/dialog/oauth?{params}"
    return HTMLResponse(f"""
    <html><body style="font-family:sans-serif;max-width:600px;margin:40px auto;padding:20px">
    <h2>Instagram Agent Setup</h2>
    <p>Click the button below to connect your Facebook Page and get your access token automatically.</p>
    <a href="{oauth_url}" style="background:#1877f2;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-size:16px">
      Connect Facebook Page
    </a>
    </body></html>
    """)


@app.get("/auth/callback")
def auth_callback(code: str = None, error: str = None):
    if error:
        return HTMLResponse(f"<h1>Error: {error}</h1>")
    if not code:
        return HTMLResponse("<h1>No code received</h1>")

    app_secret = os.environ.get("META_APP_SECRET", "")

    # Exchange code for user token
    token_resp = httpx.get(
        "https://graph.facebook.com/v21.0/oauth/access_token",
        params={
            "client_id": APP_ID,
            "client_secret": app_secret,
            "redirect_uri": CALLBACK_URL,
            "code": code,
        },
    )
    token_data = token_resp.json()
    user_token = token_data.get("access_token", "")

    if not user_token:
        return HTMLResponse(f"<h1>Token exchange failed</h1><pre>{json.dumps(token_data, indent=2)}</pre>")

    # Get pages and their Page Access Tokens
    pages_resp = httpx.get(
        "https://graph.facebook.com/v21.0/me/accounts",
        params={"access_token": user_token, "fields": "id,name,access_token,instagram_business_account"},
    )
    pages = pages_resp.json().get("data", [])

    pages_html = ""
    for page in pages:
        page_token = page.get("access_token", "")
        page_name = page.get("name", "")
        page_id = page.get("id", "")
        ig = page.get("instagram_business_account", {})
        ig_id = ig.get("id", "N/A")
        pages_html += f"""
        <div style="border:1px solid #ddd;padding:16px;margin:12px 0;border-radius:8px">
          <b>Page:</b> {page_name} (ID: {page_id})<br>
          <b>Instagram Account ID:</b> {ig_id}<br><br>
          <b>IG_PAGE_ID</b> → set to: <code>{page_id}</code><br><br>
          <b>IG_ACCESS_TOKEN</b> → copy this token:<br>
          <textarea style="width:100%;height:80px;font-size:12px">{page_token}</textarea>
        </div>
        """

    if not pages:
        pages_html = """
        <div style="border:1px solid red;padding:16px;border-radius:8px;color:red">
          No Facebook Pages found. Make sure your Instagram account is connected to your Facebook Page
          via Instagram Settings → Accounts Center → Connected accounts → Facebook.
        </div>
        """

    return HTMLResponse(f"""
    <html><body style="font-family:sans-serif;max-width:700px;margin:40px auto;padding:20px">
    <h2>Setup Complete</h2>
    {pages_html}
    <hr>
    <h3>What to do next:</h3>
    <ol>
      <li>Copy the <b>IG_ACCESS_TOKEN</b> from the box above</li>
      <li>Update your <code>.env</code> file with it</li>
      <li>Tell Claude to push the new token to Railway</li>
    </ol>
    </body></html>
    """)


# ---------------------------------------------------------------------------
# Webhook
# ---------------------------------------------------------------------------
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
