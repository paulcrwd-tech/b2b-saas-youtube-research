"""
YouTube Transcript Collector
-----------------------------
Fetches transcripts for a list of YouTube videos and saves them
into research/youtube-transcripts/<author-slug>/<video-id>.md

Usage:
    pip install youtube-transcript-api --break-system-packages
    python fetch_transcripts.py

Edit VIDEOS below (or load from videos.json) with the videos you want.
"""

import json
import os
import re
from datetime import datetime

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    raise SystemExit(
        "Missing dependency. Run:\n"
        "  pip install youtube-transcript-api --break-system-packages"
    )

OUTPUT_DIR = "research/youtube-transcripts"

# ---------------------------------------------------------------------------
# Fill this in with real videos. Each entry needs:
#   author       -> used for folder name (will be slugified)
#   video_id     -> the 11-char ID from the YouTube URL (?v=XXXXXXXXXXX)
#   title        -> video title (for the saved file header)
#   url          -> full YouTube URL (for reference)
#   published    -> approx publish date, e.g. "2026-06-01" (fill what you know)
# ---------------------------------------------------------------------------
VIDEOS = [
    {
        "author": "Dan Martell",
        "video_id": "QfxOXEbUjwI",
        "title": "The Ultimate Guide to Demand Generation for SaaS",
        "url": "https://www.youtube.com/watch?v=QfxOXEbUjwI",
        "published": "2022-08-03",
    },
    {
        "author": "Rob Walling",
        "video_id": "bUeeVU-OoCM",
        "title": "SaaS Marketing Strategies That Actually Work in 2026",
        "url": "https://www.youtube.com/watch?v=bUeeVU-OoCM",
        "published": "2025-02-16",
    },
    {
        "author": "Rob Walling",
        "video_id": "rvAUupZ_Pdc",
        "title": "What's ACTUALLY Happening in SaaS Right Now",
        "url": "https://www.youtube.com/watch?v=rvAUupZ_Pdc",
        "published": "2025-12-21",
    },
    {
        "author": "Rob Walling",
        "video_id": "1p95mVJxnRg",
        "title": "This Is the SMARTEST SaaS Marketing Strategy I've Ever Seen",
        "url": "https://www.youtube.com/watch?v=1p95mVJxnRg",
        "published": "unknown",
    },
    {
        "author": "Simon Hoiberg",
        "video_id": "fnOQMT2EYbg",
        "title": "How to build your DREAM SaaS business in 2026",
        "url": "https://www.youtube.com/watch?v=fnOQMT2EYbg",
        "published": "2026-01-19",
    },
    {
        "author": "Simon Hoiberg",
        "video_id": "aRVidOgfIYo",
        "title": "This AI agent makes you a Top Voice on social media (AgentKit + FeedHive MCP)",
        "url": "https://www.youtube.com/watch?v=aRVidOgfIYo",
        "published": "2025-10-23",
    },
    {
        "author": "Simon Hoiberg",
        "video_id": "7NYWlzytHFM",
        "title": "Winning Startups Are Changing To These Tools (here's why)",
        "url": "https://www.youtube.com/watch?v=7NYWlzytHFM",
        "published": "2025-07-21",
    },
    {
        "author": "Marc Lou",
        "video_id": "UTjU_30SHIo",
        "title": "I documented my SaaS journey to $20K MRR",
        "url": "https://www.youtube.com/watch?v=UTjU_30SHIo",
        "published": "2026-06-09",
    },
    {
        "author": "Marc Lou",
        "video_id": "JKFmLdoLm8M",
        "title": "I made $1M in 2025 (WRAPPED)",
        "url": "https://www.youtube.com/watch?v=JKFmLdoLm8M",
        "published": "2026-01-05",
    },
    {
        "author": "Marc Lou",
        "video_id": "uAdaHO7D4xw",
        "title": "Day 494 growing my SaaS startup to $1M",
        "url": "https://www.youtube.com/watch?v=uAdaHO7D4xw",
        "published": "2026-04-02",
    },
    {
        "author": "Nathan Latka",
        "video_id": "lFX0n3uYTkw",
        "title": "$1M in 3 Months Selling AI Agents?",
        "url": "https://www.youtube.com/watch?v=lFX0n3uYTkw",
        "published": "2026-05-13",
    },
    {
        "author": "Nathan Latka",
        "video_id": "UavacWr2jbQ",
        "title": "He Gave His AI Note Taker for Free and Hit $30M/yr",
        "url": "https://www.youtube.com/watch?v=UavacWr2jbQ",
        "published": "2026-05-21",
    },
    {
        "author": "TK Kader",
        "video_id": "AkdiTRGFc18",
        "title": "How To Create a Go To Market Strategy (2026 Playbook)",
        "url": "https://www.youtube.com/watch?v=AkdiTRGFc18",
        "published": "2026-02-01",
    },
    {
        "author": "Arvid Kahl",
        "video_id": "PWF_1_r0Dl8",
        "title": "439: The Increasing Risk of Building in Public",
        "url": "https://www.youtube.com/watch?v=PWF_1_r0Dl8",
        "published": "2026-04-03",
    },
    {
        "author": "Jason Lemkin",
        "video_id": "I-R1bc1rlFs",
        "title": "We replaced our sales team with 20 AI agents—here's what happened next",
        "url": "https://www.youtube.com/watch?v=I-R1bc1rlFs",
        "published": "2026-01-01",
    },
    {
        "author": "Justin Kan",
        "video_id": "oke4-jNrpCA",
        "title": "The New Way to Build Startups in 2026 (AI is Replacing This)",
        "url": "https://www.youtube.com/watch?v=oke4-jNrpCA",
        "published": "2026-06-05",
    },
    {
        "author": "Justin Kan",
        "video_id": "rnKUGHRJJWg",
        "title": "The Ultimate Q&A for Entrepreneurs | Startup Advice with Justin Kan",
        "url": "https://www.youtube.com/watch?v=rnKUGHRJJWg",
        "published": "2022-03-28",
    },
]


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def fetch_transcript(video_id: str):
    """Returns transcript as a list of {text, start, duration} dicts."""
    ytt_api = YouTubeTranscriptApi()
    fetched = ytt_api.fetch(video_id)
    return fetched.to_raw_data()


def format_transcript_md(entry: dict, transcript: list) -> str:
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
    ]
    full_text = " ".join(seg["text"].replace("\n", " ") for seg in transcript)
    lines.append(full_text)
    return "\n".join(lines)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = []

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
            transcript = fetch_transcript(entry["video_id"])
            content = format_transcript_md(entry, transcript)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[saved] {out_path}")
            results.append({"status": "ok", "path": out_path})
        except Exception as e:
            print(f"[error] {entry['author']} — {entry['video_id']}: {e}")
            results.append({"status": "error", "video_id": entry["video_id"], "error": str(e)})

    print("\nSummary:")
    ok = sum(1 for r in results if r["status"] == "ok")
    err = sum(1 for r in results if r["status"] == "error")
    print(f"  Success: {ok}")
    print(f"  Failed:  {err}")


if __name__ == "__main__":
    main()