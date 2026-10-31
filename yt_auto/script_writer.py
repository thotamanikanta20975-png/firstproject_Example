"""Writes a video with Claude, following the youtube-agent-skill workflow:

1. Package: 5 hooks (from the 21 formulas) + 10 title/thumbnail pairings.
2. Score: hookscore.py picks the hook, title.py picks the pairing.
3. Script: the full script built around the winners.
"""
import json

import anthropic

from . import skills

MODEL = "claude-opus-5-5"

PACKAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "hooks": {"type": "array", "items": {"type": "string"},
                  "description": "Exactly 5 spoken opening lines, 9-24 words each."},
        "packages": {
            "type": "array",
            "description": "Exactly 10 title + thumbnail pairings.",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "thumbnail_text": {"type": "string"},
                },
                "required": ["title", "thumbnail_text"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["hooks", "packages"],
    "additionalProperties": False,
}

SCRIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "description": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "search_queries": {"type": "array", "items": {"type": "string"},
                           "description": "The 3 searches this video should win."},
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "section": {"type": "string", "description": "Chapter name, 3-5 words."},
                    "narration": {"type": "string"},
                    "on_screen_text": {"type": "string", "description": "Max ~12 words."},
                },
                "required": ["section", "narration", "on_screen_text"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["description", "tags", "search_queries", "scenes"],
    "additionalProperties": False,
}

BASE = """You make videos for a faceless educational YouTube channel. The content
must be original, accurate and useful so it qualifies for the YouTube Partner
Program: no reused, misleading or clickbait content.
Never invent a number, a result, a quote or a source. If a figure would help and
you are not sure of it, write the line without it."""


def _system():
    voice = skills.voice_profile()
    return BASE + (f"\n\nWrite in this creator's voice:\n{voice}" if voice else "")


def _ask(client, schema, prompt):
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=32000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": schema}},
        system=_system(),
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        response = stream.get_final_message()
    if response.stop_reason == "refusal":
        raise RuntimeError(f"Claude declined this topic: {response.stop_details}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Output was cut off; try a narrower topic.")
    return json.loads(next(b.text for b in response.content if b.type == "text"))


def write_script(topic: str, fmt: str = "short", language: str = "English") -> dict:
    client = anthropic.Anthropic()
    length = ("about 45 seconds (6-8 scenes), a YouTube Short" if fmt == "short"
              else "about 6-8 minutes (30-45 scenes) with 4-7 sections")

    # 1. Packaging (yt-script hooks + yt-package pairings)
    pkg = _ask(client, PACKAGE_SCHEMA, f"""Topic: {topic}
Format: {length}. Language: {language}.

Write 5 hooks using different formulas below. A hook is the first 15 seconds:
confirm the title's promise, open a question the viewer can't close, prove the
payoff exists. Say "you" early. Prefer a number, name or date over adjectives.

{skills.hook_formulas()}

Then 10 title + thumbnail pairings. The title and thumbnail are ONE unit:
- title under 60 characters, subject in the first 40
- thumbnail text max 3 words and must NOT repeat any title word
- at most 2 all-caps words; no vague words like amazing/ultimate/secret""")

    # 2. Score with the skill's tools
    hooks = skills.rank_hooks(pkg["hooks"])
    packages = skills.rank_packages(pkg["packages"])
    hook, package = hooks[0], packages[0]

    # 3. Script around the winners (yt-script shape + yt-seo description)
    script = _ask(client, SCRIPT_SCHEMA, f"""Topic: {topic}
Format: {length}. Language: {language}.
Title: {package['title']}
The first scene's narration must be exactly this hook: {hook['hook']}

Shape:
- Scene 2 is the turn: say in one sentence what the video will do, and start doing it.
  No channel intro, no "before we get started", no subscribe pitch early.
- Body: one idea per scene, 1-3 sentences, with on-screen text for each.
- Payoff: deliver what the hook promised, and say that you are delivering it.
- Close: one ask only (subscribe).

Description: the first two lines say what the viewer gets, using the words they
would search. Then a short paragraph on what is covered and who it is for.
Tags: up to 15, only spellings/names/abbreviations people actually type.""")

    script.update(title=package["title"], thumbnail_text=package["thumbnail_text"],
                  hook_report=hooks, package_report=packages[:3])
    return script
