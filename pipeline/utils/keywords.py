"""
utils/keywords.py — single source of truth for loading tracked keywords.
"""
import os
from pathlib import Path

KEYWORDS_FILE = str(Path(__file__).parent.parent.parent / "keywords.txt")  # fusehealth/keywords.txt


def load_tracked_keywords(path: str = KEYWORDS_FILE) -> list[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()
    except FileNotFoundError:
        return []

    seen = set()
    keywords = []
    for line in raw_lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if " #" in line:
            line = line.split(" #", 1)[0].strip()
        if not line:
            continue
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        keywords.append(line)
    return keywords
