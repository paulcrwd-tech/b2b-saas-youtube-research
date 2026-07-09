"""
YouTube Transcript Collector (yt-dlp version)
-----------------------------------------------
Uses yt-dlp to download auto-generated captions, which tends to be more
resilient against YouTube's IP blocking than youtube-transcript-api.

Usage:
    pip install yt-dlp --break-system-packages
    python fetch_transcripts_ytdlp.py
"""

import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime

OUTPUT_DIR = "research/youtube-transcripts"

VIDEOS = [
    {"author": "Dan Martell", "video_id": "QfxOXEbUjwI", "title": "The Ultimate Guide to Demand Generation for SaaS", "url": "https://www.youtube.com/watch?v=QfxOXEbUjwI", "published": "2022-08-03"},
    {"author": "Rob Walling", "video_id": "bUeeVU-OoCM", "title": "SaaS Marketing Strategies That Actually Work in 2026", "url": "https://www.youtube.com/watch?v=bUeeVU-OoCM", "published": "2025-02-16"},
    {"author": "Rob Walling", "video_id": "rvAUupZ_Pdc", "title": "What's ACTUALLY Happening in SaaS Right Now", "url": "https://www.youtube.com/watch?v=rvAUupZ_Pdc", "published": "2025-12-21"},
    {"author": "Rob Walling", "video_id": "1p95mVJxnRg", "title": "This Is the SMARTEST SaaS Marketing Strategy I've Ever Seen", "url": "https://www.youtube.com/watch?v=1p95mVJxnRg", "published": "unknown"},
    {"author": "Simon Hoiberg", "video_id": "fnOQMT2EYbg", "title": "How to build your DREAM SaaS business in 2026", "url": "https://www.youtube.com/watch?v=fnOQMT2EYbg", "published": "2026-01-19"},
    {"author": "Simon Hoiberg", "video_id": "aRVidOgfIYo", "title": "This AI agent makes you a Top Voice on social media (AgentKit + FeedHive MCP)", "url": "https://www.youtube.com/watch?v=aRVidOgfIYo", "published": "2025-10-23"},
    {"author": "Simon Hoiberg", "video_id": "7NYWlzytHFM", "title": "Winning Startups Are Changing To These Tools (here's why)", "url": "https://www.youtube.com/watch?v=7NYWlzytHFM", "published": "2025-07-21"},
    {"author": "Marc Lou", "video_id": "UTjU_30SHIo", "title": "I documented my SaaS journey to $20K MRR", "url": "https://www.youtube.com/watch?v=UTjU_30SHIo", "published": "2026-06-09"},
    {"author": "Marc Lou", "video_id": "JKFmLdoLm8M", "title": "I made $1M in 2025 (WRAPPED)", "url": "https://www.youtube.com/watch?v=JKFmLdoLm8M", "published": "2026-01-05"},
    {"author": "Marc Lou", "video_id": "uAdaHO7D4xw", "title": "Day 494 growing my SaaS startup to $1M", "url": "https://www.youtube.com/watch?v=uAdaHO7D4xw", "published": "2026-04-02"},
    {"author": "Nathan Latka", "video_id": "lFX0n3uYTkw", "title": "$1M in 3 Months Selling AI Agents?", "url": "https://www.youtube.com/watch?v=lFX0n3uYTkw", "published": "2026-05-13"},
    {"author": "Nathan Latka", "video_id": "UavacWr2jbQ", "title": "He Gave His AI Note Taker for Free and Hit $30M/yr", "url": "https://www.youtube.com/watch?v=UavacWr2jbQ", "published": "2026-05-21"},
    {"author": "TK Kader", "video_id": "AkdiTRGFc18", "title": "How To Create a Go To Market Strategy (2026 Playbook)", "url": "https://www.youtube.com/watch?v=AkdiTRGFc18", "published": "2026-02-01"},
    {"author": "Arvid Kahl", "video_id": "PWF_1_r0Dl8", "title": "439: The Increasing Risk of Building in Public", "url": "https://www.youtube.com/watch?v=PWF_1_r0Dl8", "published": "2026-04-03"},
    {"author": "Jason Lemkin", "video_id": "I-R1bc1rlFs", "title": "We replaced our sales team with 20 AI agents—here's what happened next", "url": "https://www.youtube.com/watch?v=I-R1bc1rlFs", "published": "2026-01-01"},
    {"author": "Justin Kan", "video_id": "oke4-jNrpCA", "title": "The New Way to Build Startups in 2026 (AI is Replacing This)", "url": "https://www.youtube.com/watch?v=oke4-jNrpCA", "published": "2026-06-05"},
    {"author": "Justin Kan", "video_id": "rnKUGHRJJWg", "title": "The Ultimate Q&A for Entrepreneurs | Startup Advice with Justin Kan", "url": "https://www.youtube.com/watch?v=rnKUGHRJJWg", "published": "2022-03-28"},
]


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def vtt_to_text(vtt_path: str) -> str:
    """Strip VTT timestamps/formatting, return plain transcript text."""
    with open(vtt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    text_lines = []
    seen = set()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if "-->" in line:
            continue
        if re.match(r"^\d+$", line):
            continue
        clean = re.sub(r"<[^>]+>", "", line)
        clean = clean.strip()
        if clean and clean not in seen:
            text_lines.append(clean)
            seen.add(clean)

    return " ".join(text_lines)


def fetch_transcript(entry: dict, tmp_dir: str, max_retries: int = 3) -> str:
    out_template = os.path.join(tmp_dir, entry["video_id"])
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--skip-download",
        "--write-auto-sub",
        "--write-sub",
        "--sub-lang", "en",
        "--sub-format", "vtt",
        "-o", out_template,
        entry["url"],
    ]

    last_error = None
    for attempt in range(1, max_retries + 1):
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            for fname in os.listdir(tmp_dir):
                if fname.startswith(entry["video_id"]) and fname.endswith(".vtt"):
                    return vtt_to_text(os.path.join(tmp_dir, fname))
            raise RuntimeError("No .vtt file produced (video may have no captions)")

        stderr = result.stderr or result.stdout or ""
        last_error = stderr[-500:]

        if "429" in stderr or "Too Many Requests" in stderr:
            wait = 30 * attempt + random.randint(5, 15)
            print(f"    [rate-limited] waiting {wait}s before retry {attempt}/{max_retries}...")
            time.sleep(wait)
            continue
        else:
            break

    raise RuntimeError(last_error or "yt-dlp failed with no output")


def format_transcript_md(entry: dict, transcript_text: str) -> str:
    lines = [
        f"# {entry['title']}",
        "",
        f"- **Author:** {entry['author']}",
        f"- **URL:** {entry['url']}",
        f"- **Published:** {entry.get('published', 'unknown')}",
        f"- **Collected:** {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "---",
        "",
        "## Transcript",
        "",
        transcript_text,
    ]
    return "\n".join(lines)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ok, err = 0, 0

    with tempfile.TemporaryDirectory() as tmp_dir:
        for entry in VIDEOS:
            author_slug = slugify(entry["author"])
            author_dir = os.path.join(OUTPUT_DIR, author_slug)
            os.makedirs(author_dir, exist_ok=True)
            out_path = os.path.join(author_dir, f"{entry['video_id']}.md")

            if os.path.exists(out_path):
                print(f"[skip] Already collected: {out_path}")
                continue

            try:
                print(f"[fetching] {entry['author']} — {entry['title']}")
                text = fetch_transcript(entry, tmp_dir)
                content = format_transcript_md(entry, text)
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"[saved] {out_path}")
                ok += 1
            except Exception as e:
                print(f"[error] {entry['author']} — {entry['video_id']}: {e}")
                err += 1

            pause = random.randint(15, 25)
            print(f"    (waiting {pause}s before next video...)")
            time.sleep(pause)

    print(f"\nSummary:\n  Success: {ok}\n  Failed:  {err}")


if __name__ == "__main__":
    main()
