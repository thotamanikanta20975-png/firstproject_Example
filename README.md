# YouTube Automation

Turns a topic into a ready-to-upload YouTube video, using the
[youtube-agent-skill](https://github.com/Jakeschincariol/youtube-agent-skill)
pack (installed in `.claude/skills/`, MIT licence):

1. **Hook + packaging** – Claude drafts 5 hooks from the skill's 21 hook formulas
   and 10 title/thumbnail pairings. The skill's `hookscore.py` picks the strongest
   hook and `title.py` picks the best title + thumbnail pairing.
2. **Script** – Claude writes the script around the winners, following the
   `/yt-script` shape (hook, turn, one idea per beat, payoff, one ask) and the
   `/yt-seo` description rules.
3. **Voice** – free neural text-to-speech (edge-tts).
4. **Video** – caption slides + voice stitched into an MP4 with ffmpeg
   (vertical 1080×1920 for Shorts, or 1920×1080 for long videos), plus a
   thumbnail, captions file and (long videos) chapters checked against the
   `/yt-chapters` rules.
5. **Upload** – YouTube Data API, private by default, with optional scheduling.

## Setup

```bash
pip install -r requirements.txt        # also install ffmpeg
export ANTHROPIC_API_KEY=sk-ant-...    # from console.anthropic.com
```

For uploading: in Google Cloud Console create a project, enable
**YouTube Data API v3**, create an **OAuth client ID (Desktop app)** and save it
as `client_secret.json` in this folder. The first upload asks you to log in.

## Usage

```bash
python main.py make "5 surprising facts about octopuses"
python main.py make "How compound interest works" --format long
python main.py make "Benefits of yoga" --language Hindi --voice hi-IN-MadhurNeural
python main.py batch topics.txt                      # one topic per line
python main.py upload output/5-surprising-facts-about-octopuses
python main.py upload output/<folder> --publish-at 2026-11-02T15:00:00Z
```

Each video lands in `output/<topic>/`:

| file | what it is |
| --- | --- |
| `video.mp4` | the video |
| `thumbnail.png` | 1280×720 thumbnail (uploaded automatically if your channel is verified) |
| `captions.srt` | subtitles |
| `metadata.json` | title, description, tags |
| `review.md` | every hook and title with its skill score – read this first |

**Watch every video and fact-check it before publishing.** As the skill says:
ship it, or change it?

### Your voice (recommended)

Copy `templates/voice.md` to `voice.md` (or `~/.claude/youtube/voice.md`) and
fill it in. Claude writes every script in that voice.

### The other skills (in Claude Code)

Open this repo in Claude Code and the skills are available as commands:
`/yt-plan` (weekly plan), `/yt-viral` (what's working in your niche),
`/yt-retention` (read your retention export), `/yt-comment` (reply to comments),
`/yt-shorts` (cut Shorts from a long video), `/yt-audit` (one fix for your channel),
plus `/yt-script`, `/yt-package`, `/yt-seo`, `/yt-chapters`, `/yt-edit`.

## How to actually earn money

YouTube pays through the **YouTube Partner Program (YPP)**. You need roughly:
- 1,000 subscribers **and** either 4,000 public watch hours (last 12 months)
  or 10 million Shorts views (last 90 days).

Things that get automated channels **rejected or demonetized**:
- "Inauthentic / mass-produced" content: near-identical template videos with
  no added value. Vary topics, add your own insight, and edit the scripts.
- Reused content (clips, other people's videos, text read word-for-word from sites).
- Not disclosing realistic AI-generated content (the uploader marks videos as
  containing synthetic media for you).
- Fake views, sub-for-sub, bought subscribers – never do this; it gets channels banned.

Tips that help:
- Pick one niche (finance basics, science facts, history, tech tips) and post
  consistently, e.g. 1 Short per day + 1 long video per week.
- Long videos earn much more per view than Shorts; use Shorts to grow subscribers.
- Improve visuals over time (stock footage from Pexels, your own images).
- Other income once you grow: affiliate links in descriptions, sponsorships.

Earnings are never guaranteed; most channels take months to qualify.

## Costs

Claude API: a few cents per Short script. edge-tts and the YouTube API are free
(YouTube's default quota allows about 6 uploads per day).
