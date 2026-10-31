# YouTube Automation

Turns a topic into a ready-to-upload YouTube video:

1. **Script** – Claude writes the title, description, tags and narration.
2. **Voice** – free neural text-to-speech (edge-tts).
3. **Video** – caption slides + voice stitched into an MP4 with ffmpeg
   (vertical 1080×1920 for Shorts, or 1920×1080 for long videos).
4. **Upload** – YouTube Data API, private by default, with optional scheduling.

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

Each video lands in `output/<topic>/` with `video.mp4` and `metadata.json`.
**Watch every video and fact-check it before publishing.**

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
