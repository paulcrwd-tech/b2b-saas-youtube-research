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
    {"author": "Marc Lou", "video_id": "UTjU_30SHIo", "title": "I documented my