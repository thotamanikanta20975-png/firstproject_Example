"""Bridge to the installed youtube-agent-skill tools in .claude/skills/.

Uses the skill's own scorers so every video goes through the same checks a
creator would run by hand:
  yt-script/hookscore.py  -> pick the strongest hook
  yt-package/title.py     -> lint title + thumbnail as one pairing
  yt-chapters rules       -> only emit chapters YouTube will render
"""
import importlib.util
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, ".claude", "skills")


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SKILLS, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hookscore = _load("yt-script/hookscore.py", "hookscore")
title_lint = _load("yt-package/title.py", "title_lint")


def hook_formulas() -> str:
    """The 21 formulas from hooks.json, condensed for the prompt."""
    with open(os.path.join(SKILLS, "yt-script", "hooks.json")) as f:
        data = json.load(f)
    rules = "\n".join(f"- {r}" for r in data["rules"])
    forms = "\n".join(f"- {h['name']}: {h['shape']} Fails when: {h['fails_when']}"
                      for h in data["hooks"])
    return f"Rules:\n{rules}\n\nFormulas:\n{forms}"


def rank_hooks(hooks: list) -> list:
    out = []
    for h in hooks:
        parts, verdict, formula, _ = hookscore.score(h)
        out.append({"hook": h, "verdict": verdict, "band": hookscore.band(verdict),
                    "formula": formula, "properties": parts})
    return sorted(out, key=lambda r: -r["verdict"])


def rank_packages(pairs: list) -> list:
    """pairs: [{"title": ..., "thumbnail_text": ...}]"""
    out = []
    for p in pairs:
        r = title_lint.check(p["title"], p["thumbnail_text"])
        r["thumbnail_text"] = p["thumbnail_text"]
        out.append(r)
    return sorted(out, key=lambda r: -r["score"])


def voice_profile() -> str | None:
    """voice.md from the skill's location, or the project folder."""
    for path in (os.path.expanduser("~/.claude/youtube/voice.md"),
                 os.path.join(ROOT, "voice.md")):
        if os.path.exists(path):
            with open(path) as f:
                return f.read()
    return None


def mmss(t):
    t = int(t)
    h, m, s = t // 3600, (t % 3600) // 60, t % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def chapters(scenes: list, durations: list) -> str | None:
    """Chapters from script sections, checked against yt-chapters' rules:
    first at 0:00, at least 3, each at least 10 seconds. Returns None if invalid."""
    marks, t = [], 0.0
    for scene, d in zip(scenes, durations):
        sec = scene.get("section", "").strip()
        if sec and (not marks or marks[-1][1] != sec):
            marks.append([t, sec])
        t += d
    if not marks:
        return None
    marks[0][0] = 0.0
    ends = [m[0] for m in marks[1:]] + [t]
    if len(marks) < 3 or any(e - m[0] < 10 for m, e in zip(marks, ends)):
        return None
    return "\n".join(f"{mmss(s)} {name}" for s, name in marks)


def srt(scenes: list, durations: list) -> str:
    def ts(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    lines, t = [], 0.0
    for i, (scene, d) in enumerate(zip(scenes, durations), 1):
        lines += [str(i), f"{ts(t)} --> {ts(t + d)}", scene["narration"], ""]
        t += d
    return "\n".join(lines)
