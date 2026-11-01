"""Lightweight diff vs hand-written T1 Listing Pack (polish notes only).

Wording differences never flip ``listable``; they become
``human_review_required`` items for operators to polish.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

DEFAULT_T1 = Path("/workspace/T1-Listing-Pack-v0-drawer-organizer.md")

# Section headers in the hand pack map to market keys used by adapters.
_SECTION_MARKERS = {
    "amazon_us": r"## A\) Amazon US",
    "shopee_id": r"## B\) Shopee Indonesia",
    "meli_mx": r"## C\) Mercado Libre MX",
}


def _extract_fenced_after(text: str, heading_pat: str, fence_after: str) -> str | None:
    """Find a ``` block that follows ``fence_after`` within a section."""
    m = re.search(heading_pat, text)
    if not m:
        return None
    # next section starts at ## [A-E] or end
    rest = text[m.end() :]
    next_sec = re.search(r"\n## [A-E0]\)", rest)
    section = rest[: next_sec.start()] if next_sec else rest
    # Prefer the first fenced block after the label (Title / Judul / Título)
    label = re.search(fence_after, section, flags=re.IGNORECASE)
    chunk = section[label.end() :] if label else section
    fm = re.search(r"```\n(.*?)\n```", chunk, flags=re.DOTALL)
    if not fm:
        return None
    return fm.group(1).strip()


def extract_t1_titles(t1_path: Path | str | None = None) -> dict[str, str]:
    path = Path(t1_path) if t1_path else DEFAULT_T1
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    out: dict[str, str] = {}
    labels = {
        "amazon_us": r"### Title",
        "shopee_id": r"### Judul",
        "meli_mx": r"### T[ií]tulo",
    }
    for market, sec in _SECTION_MARKERS.items():
        title = _extract_fenced_after(text, sec, labels[market])
        if title:
            out[market] = title
    return out


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def compare_to_t1(
    markets: dict[str, Any],
    t1_path: Path | str | None = None,
) -> list[dict[str, str]]:
    """Return human_review_required notes for title (and coarse bullet) polish."""
    notes: list[dict[str, str]] = []
    t1_titles = extract_t1_titles(t1_path)
    if not t1_titles:
        notes.append(
            {
                "severity": "all",
                "field": "t1_reference",
                "severity": "human_review_required",
                "detail": "T1 hand pack not found; skip wording compare",
            }
        )
        return notes

    for market, pack in markets.items():
        gen_title = pack.get("title") or ""
        hand = t1_titles.get(market)
        if not hand:
            notes.append(
                {
                    "severity": market,
                    "field": "title",
                    "severity": "human_review_required",
                    "detail": "No T1 title extracted for this market",
                }
            )
            continue
        if _norm(gen_title) != _norm(hand):
            notes.append(
                {
                    "marketplace": market,
                    "field": "title",
                    "severity": "human_review_required",
                    "detail": (
                        "Auto title differs from hand T1 Pack (adapter length/"
                        "style constraints). Polish if seller wants T1 wording. "
                        f"auto={gen_title!r} | t1={hand!r}"
                    ),
                }
            )
        bullets = pack.get("bullets") or []
        # Coarse signal: bullet count mismatch vs typical T1 (Amazon 5; others 6)
        expected = 5 if market == "amazon_us" else 6
        if len(bullets) != expected:
            notes.append(
                {
                    "marketplace": market,
                    "field": "bullets",
                    "severity": "human_review_required",
                    "detail": (
                        f"Bullet count {len(bullets)} vs T1-typical {expected}; "
                        "review wording vs hand pack"
                    ),
                }
            )
        else:
            notes.append(
                {
                    "marketplace": market,
                    "field": "bullets",
                    "severity": "human_review_required",
                    "detail": (
                        "Auto bullets solidified from adapters; compare to T1 "
                        "hand pack for scene/softening polish (not a gate fail)"
                    ),
                }
            )
        # Optional Amazon A+ / longer title scenes
        if market == "amazon_us":
            notes.append(
                {
                    "marketplace": market,
                    "field": "a_plus_and_long_title",
                    "severity": "human_review_required",
                    "detail": (
                        "T1 hand pack has longer ≤200-char title + A+ paragraph; "
                        "adapter enforces ≤75 title. Optional: restore scenes to "
                        "item_highlights / A+ manually."
                    ),
                }
            )
    return notes
