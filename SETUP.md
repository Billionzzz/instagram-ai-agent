# Instagram AI Agent — Setup Guide

## Architecture

```
Instagram DM → Meta Webhook → FastAPI server → Claude AI → Reply back
```

---

## Step 1: Meta Developer Setup

1. Go to https://developers.facebook.com and create an app.
2. Add the **Instagram** product to your app.
3. Connect a **Professional / Business / Creator** Instagram account.
4. Under **Instagram > API setup**, generate a **Page Access Token** — save it as `INSTAGRAM_ACCESS_TOKEN`.
5. Note your **App Secret** from App Settings → Basic — save it as `INSTAGRAM_APP_SECRET`.
6. Pick any random string for `INSTAGRAM_VERIFY_TOKEN` (e.g. `my-secret-token-123`).

---

## Step 2: Deploy to Railway

### Option A — GitHub (recommended)

1. Push this repo to GitHub.
2. Go to https://railway.app → New Project → Deploy from GitHub repo.
3. Railway auto-detects Python via Nixpacks.

### Option B — Railway CLI

```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

### Set environment variables in Railway dashboard

| Variable | Value |
|---|---|
| `GROQ_API_KEY` | Your Groq key (console.groq.com) |
| `INSTAGRAM_ACCESS_TOKEN` | Page Access Token from Meta |
| `INSTAGRAM_APP_SECRET` | App Secret from Meta |
| `INSTAGRAM_VERIFY_TOKEN` | Your chosen verify token |

Railway automatically injects `$PORT` — no need to set it.

---

## Step 3: Register the Webhook

1. In Railway, copy your public URL (e.g. `https://your-app.railway.app`).
2. In Meta Developer Console → Instagram → Webhooks:
   - **Callback URL**: `https://your-app.railway.app/webhook`
   - **Verify Token**: the value you set for `INSTAGRAM_VERIFY_TOKEN`
3. Subscribe to the **messages** field.
4. Click **Verify and Save** — Meta will call GET /webhook to confirm.

---

## Step 4: Test

Send a DM to your connected Instagram account. The agent should reply within seconds.

---

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and fill in your keys
cp .env.example .env

# Run locally
uvicorn main:app --reload --port 8000
```

Use [ngrok](https://ngrok.com) to expose localhost for webhook testing:
```bash
ngrok http 8000
# Use the ngrok URL as your webhook callback URL in Meta Developer Console
```

---

## Conversation Memory

By default, conversation history is stored in-process memory (resets on restart). For persistent memory across restarts, replace the `_conversations` dict in `agent.py` with a Redis or database store.
