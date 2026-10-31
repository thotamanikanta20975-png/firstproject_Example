"""YouTube automation: topic -> script -> voice -> video -> upload.

  python main.py make "5 surprising facts about octopuses"
  python main.py make "How compound interest works" --format long
  python main.py upload output/<folder> --publish-at 2026-11-02T15:00:00Z
  python main.py batch topics.txt
"""
import argparse
import json
import os
import re

from yt_auto import skills, video, voice
from yt_auto.script_writer import write_script


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


def review_report(meta, script):
    """What the yt-script / yt-package skills hand back, saved for a human check."""
    out = [f"# {meta['title']}", "", f"Thumbnail text: **{meta['thumbnail_text']}**", "",
           "## Hooks (scored by yt-script/hookscore.py)", ""]
    for h in script["hook_report"]:
        props = ", ".join(f"{k.lower()} {v}" for k, v in h["properties"].items())
        out.append(f"- **{h['verdict']} {h['band']}** ({h['formula']}): {h['hook']}  \n  {props}")
    out += ["", "## Top title + thumbnail pairings (linted by yt-package/title.py)", ""]
    for p in script["package_report"]:
        issues = "; ".join(f"{k}: {m}" for k, m in p["issues"]) or "no issues"
        out.append(f"- **{p['score']}/100** \"{p['title']}\" + [{p['thumbnail_text']}]: {issues}")
    out += ["", "## Searches this should win", ""] + [f"- {q}" for q in script["search_queries"]]
    out += ["", f"Runtime: {meta['runtime']}", "",
            "Watch the video and check every fact. **Ship it, or change it?**", ""]
    return "\n".join(out)


def make(topic, fmt="short", voice_name="en-US-AndrewNeural", language="English"):
    size = (1080, 1920) if fmt == "short" else (1920, 1080)
    folder = os.path.join("output", slugify(topic))
    work = os.path.join(folder, "parts")
    os.makedirs(work, exist_ok=True)

    print(f"[1/4] Hooks, titles and script: {topic}")
    script = write_script(topic, fmt, language)
    print(f"      hook {script['hook_report'][0]['verdict']}/100, "
          f"title {script['package_report'][0]['score']}/100: {script['title']}")

    print(f"[2/4] Voice + slides for {len(script['scenes'])} scenes")
    clips, durations = [], []
    for i, scene in enumerate(script["scenes"]):
        img, mp3, clip = (os.path.join(work, f"{i:03d}.{ext}") for ext in ("png", "mp3", "mp4"))
        video.render_slide(scene["on_screen_text"], img, size, i)
        voice.synthesize(scene["narration"], mp3, voice_name)
        video.make_clip(img, mp3, clip)
        clips.append(clip)
        durations.append(video.duration(clip))

    print("[3/4] Assembling video, thumbnail and captions")
    video.concat(clips, os.path.join(folder, "video.mp4"))
    video.render_thumbnail(script["thumbnail_text"], os.path.join(folder, "thumbnail.png"))
    with open(os.path.join(folder, "captions.srt"), "w") as f:
        f.write(skills.srt(script["scenes"], durations))

    desc = script["description"]
    if fmt == "long":
        chapters = skills.chapters(script["scenes"], durations)
        if chapters:
            desc += "\n\nChapters\n" + chapters
    if fmt == "short" and "#shorts" not in desc.lower():
        desc += "\n\n#shorts"
    meta = {"topic": topic, "format": fmt, "title": script["title"],
            "thumbnail_text": script["thumbnail_text"], "description": desc,
            "tags": script["tags"], "runtime": skills.mmss(sum(durations)),
            "scenes": script["scenes"]}
    with open(os.path.join(folder, "metadata.json"), "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print("[4/4] Writing review.md")
    with open(os.path.join(folder, "review.md"), "w") as f:
        f.write(review_report(meta, script))
    print(f"Done: {folder}/  (read review.md and watch video.mp4 before uploading)")
    return folder


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("make", help="create a video from a topic")
    m.add_argument("topic")
    m.add_argument("--format", choices=["short", "long"], default="short")
    m.add_argument("--voice", default="en-US-AndrewNeural", help="edge-tts voice, e.g. hi-IN-MadhurNeural")
    m.add_argument("--language", default="English")

    b = sub.add_parser("batch", help="create videos for every line in a file")
    b.add_argument("file")
    b.add_argument("--format", choices=["short", "long"], default="short")
    b.add_argument("--voice", default="en-US-AndrewNeural")
    b.add_argument("--language", default="English")

    u = sub.add_parser("upload", help="upload a made video (private by default)")
    u.add_argument("folder")
    u.add_argument("--privacy", choices=["private", "unlisted", "public"], default="private")
    u.add_argument("--publish-at", help="schedule, ISO 8601 UTC, e.g. 2026-11-02T15:00:00Z")

    a = p.parse_args()
    if a.cmd == "make":
        make(a.topic, a.format, a.voice, a.language)
    elif a.cmd == "batch":
        with open(a.file) as f:
            for topic in filter(None, (line.strip() for line in f)):
                make(topic, a.format, a.voice, a.language)
    else:
        from yt_auto.uploader import upload
        vid = upload(a.folder, a.privacy, a.publish_at)
        print(f"Uploaded: https://youtu.be/{vid}")


if __name__ == "__main__":
    main()
