#!/usr/bin/env python3
"""Resolve historical robotics brief entries against arXiv primary records.

This script is intentionally conservative: it writes candidate matches only.
A later verified pass applies direct links to the coverage index and archived posts.
"""
from __future__ import annotations

import html
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from difflib import SequenceMatcher

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "robotics-brief-covered-items.md"
OUT = ROOT / "robotics-ref-resolution.json"
ARXIV_API = "https://export.arxiv.org/api/query"
ATOM = {"a": "http://www.w3.org/2005/Atom"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower()
    s = re.sub(r"https?://\S+", " ", s)
    s = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", s)
    return " ".join(s.split())


def parse_pending() -> list[dict[str, str]]:
    text = INDEX.read_text(encoding="utf-8")
    marker = "## 历史导入待核验条目"
    if marker not in text:
        return []
    tail = text.split(marker, 1)[1].split("## 维护检查表", 1)[0]
    current_date = ""
    items: list[dict[str, str]] = []
    for raw in tail.splitlines():
        line = raw.strip()
        m = re.match(r"###\s+(\d{4}-\d{2}-\d{2})", line)
        if m:
            current_date = m.group(1)
            continue
        if not line or line.startswith(">") or line.startswith("以下条目"):
            continue
        if (current_date and "；" in line) or (current_date and line.endswith("。")):
            for item in re.split(r"[；;]", line.rstrip("。")):
                item = item.strip()
                if item and not item.startswith("注："):
                    items.append({"date": current_date, "label": item})
    seen = set()
    out = []
    for item in items:
        key = (item["date"], item["label"])
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def query_batch(labels: list[str]) -> list[dict[str, str]]:
    parts = []
    for label in labels:
        q = label.replace("/", " ").replace("+", " ")
        q = re.sub(r"[（）()]", " ", q)
        parts.append(f'all:"{q}"')
    query = " OR ".join(parts)
    params = urllib.parse.urlencode({"search_query": query, "start": 0, "max_results": 40, "sortBy": "submittedDate", "sortOrder": "descending"})
    req = urllib.request.Request(f"{ARXIV_API}?{params}", headers={"User-Agent": "helywin-daily-reference-resolver/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    results = []
    for entry in root.findall("a:entry", ATOM):
        title = " ".join((entry.findtext("a:title", default="", namespaces=ATOM)).split())
        url = entry.findtext("a:id", default="", namespaces=ATOM).replace("http://", "https://")
        published = entry.findtext("a:published", default="", namespaces=ATOM)
        summary = " ".join((entry.findtext("a:summary", default="", namespaces=ATOM)).split())
        results.append({"title": html.unescape(title), "url": url, "published": published, "summary": summary})
    return results


def score(label: str, candidate: dict[str, str]) -> float:
    a, b = norm(label), norm(candidate["title"])
    ratio = SequenceMatcher(None, a, b).ratio()
    at = set(a.split())
    bt = set(b.split())
    overlap = len(at & bt) / max(1, len(at))
    contains = 1.0 if a and a in b else 0.0
    return round(0.55 * ratio + 0.35 * overlap + 0.10 * contains, 4)


def main() -> None:
    items = parse_pending()
    resolved = []
    for i in range(0, len(items), 4):
        batch = items[i:i+4]
        labels = [x["label"] for x in batch]
        try:
            candidates = query_batch(labels)
        except Exception as exc:
            for item in batch:
                resolved.append({**item, "error": repr(exc), "candidates": []})
            time.sleep(3)
            continue
        for item in batch:
            ranked = sorted(
                ({**c, "score": score(item["label"], c)} for c in candidates),
                key=lambda x: x["score"],
                reverse=True,
            )[:5]
            resolved.append({**item, "candidates": ranked})
        time.sleep(3)
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "count": len(resolved),
        "items": resolved,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} with {len(resolved)} items")


if __name__ == "__main__":
    main()
