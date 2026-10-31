"""Turns scenes (caption + audio) into an MP4 using Pillow and ffmpeg."""
import os
import subprocess
import textwrap

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
PALETTES = [((20, 30, 70), (90, 40, 140)), ((10, 60, 60), (20, 120, 90)),
            ((70, 20, 30), (150, 60, 40)), ((30, 30, 30), (70, 70, 90))]


def _font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default(size)


def render_slide(text: str, path: str, size: tuple, index: int) -> None:
    w, h = size
    top, bottom = PALETTES[index % len(PALETTES)]
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    for y in range(h):  # vertical gradient
        t = y / h
        draw.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))

    font = _font(int(w * 0.075))
    lines = textwrap.wrap(text, width=18 if w < h else 30)
    line_h = int(font.size * 1.3)
    y = (h - line_h * len(lines)) // 2
    for line in lines:
        lw = draw.textlength(line, font=font)
        draw.text(((w - lw) / 2, y), line, font=font, fill="white",
                  stroke_width=4, stroke_fill="black")
        y += line_h
    img.save(path)


def _run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def make_clip(image: str, audio: str, out: str) -> None:
    _run(["ffmpeg", "-y", "-loop", "1", "-i", image, "-i", audio,
          "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", "30",
          "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
          "-af", "apad=pad_dur=0.3", "-shortest", out])


def concat(clips: list, out: str) -> None:
    listfile = out + ".txt"
    with open(listfile, "w") as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c)}'\n")
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile, "-c", "copy", out])
    os.remove(listfile)


def duration(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", path],
                         check=True, capture_output=True, text=True)
    return float(out.stdout.strip())


def render_thumbnail(text: str, path: str) -> None:
    """1280x720 thumbnail: max 3 big words, high contrast at feed size."""
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), (15, 15, 25))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, int(h * 0.78), w, h], fill=(230, 40, 40))
    words = text.upper().split()
    lines = textwrap.wrap(" ".join(words), width=12)
    size = 170
    font = _font(size)
    while size > 60 and max(draw.textlength(l, font=font) for l in lines) > w * 0.9:
        size -= 10
        font = _font(size)
    line_h = int(font.size * 1.1)
    y = (int(h * 0.78) - line_h * len(lines)) // 2
    for line in lines:
        lw = draw.textlength(line, font=font)
        draw.text(((w - lw) / 2, y), line, font=font, fill=(255, 220, 0),
                  stroke_width=8, stroke_fill="black")
        y += line_h
    img.save(path)
