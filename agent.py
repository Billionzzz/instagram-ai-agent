import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a friendly and helpful Instagram assistant. You help people with general questions on any topic — from everyday advice and recommendations to explaining concepts, helping with ideas, or just having a good conversation.

Keep your replies concise and conversational since this is Instagram chat. Aim for 1-3 short paragraphs at most. Be warm, approachable, and helpful. Never claim to be human if asked directly — you are an AI assistant."""

# Conversation history stored in memory (keyed by sender ID)
# For production, swap this dict for a Redis or database store
_conversations: dict[str, list[dict]] = {}


def get_reply(sender_id: str, user_message: str) -> str:
    history = _conversations.setdefault(sender_id, [])

    history.append({"role": "user", "content": user_message})

    # Keep last 20 turns to stay within context limits
    trimmed = history[-20:]

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + trimmed,
        max_tokens=1024,
    )

    reply_text = response.choices[0].message.content
    history.append({"role": "assistant", "content": reply_text})

    # Trim stored history after appending
    _conversations[sender_id] = history[-20:]

    return reply_text
