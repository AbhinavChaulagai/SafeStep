"""
LLM service — Google Gemini 1.5 Flash via google-genai SDK (free tier).
Falls back to rule-based briefing when GEMINI_API_KEY is not set.
Free tier: 15 RPM, 1M tokens/min, 1,500 requests/day.
"""
from __future__ import annotations

import json
import logging

from google import genai
from google.genai import types

from config import settings

log = logging.getLogger(__name__)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


SYSTEM_PROMPT = """You are a travel safety assistant for SafeStep, a neighborhood intelligence tool.

Given structured neighborhood data, generate a 4-5 sentence safety briefing.

Rules:
- Never use the words "safe" or "unsafe" as absolutes
- Always reference the time of day in your response
- Be specific — mention actual offense types, not vague language
- If news alerts exist, mention them explicitly with the source
- If reddit sentiment exists, reference "locals report..."
- End with one practical recommendation
- Adjust tone based on traveler_type:
  solo → emphasize awareness and nighttime caution
  family → emphasize residential calm and daytime vs nighttime difference
  couple → balanced, mention restaurant/entertainment zones
  nightlife → be direct about late-night specific risks
- Output plain prose only, no bullet points, no headers"""


async def generate_safety_briefing(context: dict) -> str:
    if not settings.gemini_api_key:
        log.debug("No Gemini key — using rule-based fallback briefing")
        return _fallback_briefing(context)
    try:
        client = _get_client()
        prompt = f"{SYSTEM_PROMPT}\n\nNeighborhood data:\n{json.dumps(context, indent=2)}"
        response = await client.aio.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=300,
                temperature=0.4,
            ),
        )
        return response.text or _fallback_briefing(context)
    except Exception as exc:
        log.warning("Gemini call failed (%s) — falling back to rule-based briefing", exc)
        return _fallback_briefing(context)


async def classify_reddit_post(post_title: str, post_body: str) -> dict:
    if not settings.gemini_api_key:
        return {"safety_relevant": False, "sentiment": "neutral", "concerns": []}
    prompt = (
        f"Classify this Reddit post about a NYC neighborhood.\n"
        f"Title: {post_title}\nBody: {post_body[:500]}\n\n"
        f'Respond with JSON only: {{"safety_relevant": true/false, '
        f'"sentiment": "positive|neutral|negative|concerned", "concerns": ["..."]}}'
    )
    try:
        client = _get_client()
        response = await client.aio.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                max_output_tokens=150,
                temperature=0.0,
            ),
        )
        return json.loads(response.text or "{}")
    except Exception as exc:
        log.warning("Reddit classification failed: %s", exc)
        return {"safety_relevant": False, "sentiment": "neutral", "concerns": []}


async def summarize_reddit_signals(posts: list[dict]) -> str:
    if not posts or not settings.gemini_api_key:
        return ""
    joined = "\n".join(f"- {p['post_title']}" for p in posts[:10])
    try:
        client = _get_client()
        response = await client.aio.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"Summarize these Reddit posts about neighborhood safety in one sentence:\n{joined}",
            config=types.GenerateContentConfig(max_output_tokens=80, temperature=0.3),
        )
        return response.text or ""
    except Exception:
        return ""


# ── rule-based fallback ───────────────────────────────────────────────────────

def _fallback_briefing(ctx: dict) -> str:
    n = ctx.get("neighborhood", "This area")
    band = ctx.get("risk_band", "Moderate")
    time = ctx.get("time_requested", "evening").replace("_", " ")
    traveler = ctx.get("traveler_type", "solo")
    stats = ctx.get("crime_stats", {})
    violent = stats.get("violent_rate", 0)
    theft = stats.get("theft_rate", 0)
    trend = stats.get("yoy_trend", "")
    news = ctx.get("news_signals", [])
    reddit = ctx.get("reddit_sentiment", {})
    nearby = ctx.get("nearby_safer", [])

    parts: list[str] = []

    parts.append(
        f"{n} shows a {band.lower()} risk level during {time} hours, "
        f"with violent incidents at {violent:.1f} per 1,000 residents "
        f"and theft at {theft:.1f} per 1,000 residents."
    )

    if trend:
        parts.append(f"Crime here is trending {trend}.")

    if news:
        parts.append(f"Recent alerts include: {news[0]}.")

    reddit_count = reddit.get("post_count_30d", 0)
    if reddit_count > 0:
        sentiment = reddit.get("dominant_sentiment", "neutral")
        parts.append(
            f"Locals report {sentiment} sentiment across "
            f"{reddit_count} community discussions in the past 30 days."
        )

    high_risk = band in ("Elevated", "High")
    if traveler == "solo":
        parts.append(
            "Solo travelers should stay on well-lit main streets and remain alert during these hours."
            if high_risk
            else f"Solo travelers will generally find this area manageable during {time} hours."
        )
    elif traveler == "family":
        parts.append(
            "Families are advised to plan daytime activities and limit late-night excursions here."
            if high_risk
            else "Families should find this neighborhood comfortable for daytime and early evening visits."
        )
    elif traveler == "couple":
        parts.append(
            "Couples can enjoy local dining and entertainment — keep to populated, well-lit streets."
        )
    elif traveler == "nightlife":
        parts.append(
            "Nightlife visitors should travel in groups and use rideshare services when heading home late."
            if high_risk
            else "Typical nightlife precautions apply — stay with your group and plan your route home."
        )

    if nearby:
        parts.append(f"Lower-risk alternatives nearby include {', '.join(nearby[:2])}.")

    return " ".join(parts)
