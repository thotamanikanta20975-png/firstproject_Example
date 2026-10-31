"""Writes a video script (title, description, tags, scenes) with Claude."""
import json

import anthropic

MODEL = "claude-opus-5-5"

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Under 70 characters, honest, curiosity-driven."},
        "description": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "narration": {"type": "string", "description": "What the voice says."},
                    "on_screen_text": {"type": "string", "description": "Short caption, max ~12 words."},
                },
                "required": ["narration", "on_screen_text"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "description", "tags", "scenes"],
    "additionalProperties": False,
}

SYSTEM = """You write scripts for a faceless educational YouTube channel.
Make content that is original, accurate and useful, so it qualifies for the
YouTube Partner Program (no reused, misleading or clickbait content).
Open with a strong hook in the first scene. Each scene is 1-3 sentences.
Do not invent statistics or quotes; if unsure of a fact, leave it out.
End with a short call to subscribe."""


def write_script(topic: str, fmt: str = "short", language: str = "English") -> dict:
    length = (
        "about 45 seconds of narration (6-8 scenes), for YouTube Shorts"
        if fmt == "short"
        else "about 5-7 minutes of narration (25-40 scenes)"
    )
    client = anthropic.Anthropic()
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=32000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={
            "effort": "medium",
            "format": {"type": "json_schema", "schema": SCHEMA},
        },
        system=SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Topic: {topic}\nLength: {length}\nLanguage: {language}",
        }],
    ) as stream:
        response = stream.get_final_message()

    if response.stop_reason == "refusal":
        raise RuntimeError(f"Claude declined this topic: {response.stop_details}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Script was cut off; try a narrower topic.")
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)
