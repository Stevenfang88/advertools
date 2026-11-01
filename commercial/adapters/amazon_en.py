"""Amazon US (EN) listing adapter — title ≤75, 5 bullets, backend ≤249 bytes."""
from __future__ import annotations

from typing import Any

from .compliance_gate import gate_listing, load_rules

MARKET = "amazon_us"


def _size_summary(sku: dict[str, Any]) -> str:
    n = len(sku.get("sizes") or [])
    return f"{n} sizes" if n else "multi-size"


def _dims_line(sku: dict[str, Any]) -> str:
    parts = []
    for s in sku.get("sizes") or []:
        d = s.get("dims_in") or {}
        parts.append(
            f"{s.get('qty')}× ({d.get('l')}×{d.get('w')}×{d.get('h')}\")"
        )
    return ", ".join(parts)


def generate(sku: dict[str, Any]) -> dict[str, Any]:
    pcs = sku.get("piece_count", 0)
    pads = sku.get("pad_count", 0)
    n_sizes = len(sku.get("sizes") or [])
    brand = sku.get("brand") or ""
    color = (sku.get("color") or "clear").title() if sku.get("color") else "Clear"
    # Prefer "Clear" marketing adjective
    color_word = "Clear" if "clear" in (sku.get("color") or "clear").lower() or "transparent" in (sku.get("color") or "").lower() else color

    # Hard ≤75 — front-load count + clear plastic + drawer organizer
    title = f"{pcs} PCS Clear Plastic Drawer Organizer Set {n_sizes} Sizes Non-Slip Pads"
    if len(title) > 75:
        title = f"{pcs} PCS Clear Drawer Organizer {n_sizes} Sizes Non-Slip Pads"
    title = title[:75].rstrip()

    # Overflow ideas go to item highlights (≤125)
    scenes = sku.get("scenes") or []
    scene_bits = []
    for s in scenes[:4]:
        # shorten scene labels for highlight
        scene_bits.append(s.replace(" drawer", "").replace("desk ", ""))
    item_highlights = (
        f"Scenes: {', '.join(scene_bits)}. "
        f"{pads} silicone pads. Nestable trays. Wipe/hand-rinse care."
    )
    if len(item_highlights) > 125:
        item_highlights = item_highlights[:125].rstrip()

    dims = _dims_line(sku)
    bullets = [
        (
            f"{pcs} trays in {n_sizes} sizes — Includes {dims} so you can mix "
            f"layouts for vanity, bathroom, kitchen, or desk drawers."
        ),
        (
            "See-through plastic — Clear trays let you spot cosmetics, jewelry, "
            "utensils, or office supplies without digging."
        ),
        (
            f"Non-slip pads included — {pads} silicone pads stick to tray corners "
            f"to reduce sliding when drawers open and close."
        ),
        (
            "Modular and nestable — Arrange side-by-side in the drawer; nest unused "
            "trays to save shelf space."
        ),
        (
            "Easy everyday care — Wipe with a damp cloth or hand-rinse with water; "
            "no tools required out of the box."
        ),
    ]
    # Clamp bullet lengths to Amazon window if somehow over
    bullets = [b if len(b) <= 255 else b[:255].rstrip() for b in bullets]

    description = (
        f"Keep drawers usable instead of chaotic. This {pcs}-piece clear drawer "
        f"organizer set gives you {n_sizes} tray sizes to fit makeup, bathroom "
        f"essentials, kitchen gadgets, and desk supplies. Crystal-clear plastic "
        f"makes contents visible at a glance; stick-on silicone pads help trays "
        f"stay put. Nest trays when not in use. Wipe clean with a damp cloth. "
        f"Home organization only — not medical storage."
    )

    # Backend: complementary stems; avoid repeating full title phrases where possible
    backend = (
        "makeup vanity bathroom kitchen office desk storage bins trays dividers "
        "nestable modular cabinet organizer silicone pads utensil jewelry cosmetic "
        "vanity tray drawer divider"
    )
    while len(backend.encode("utf-8")) > 249:
        backend = backend.rsplit(" ", 1)[0]

    keywords = [
        "drawer organizer",
        "clear drawer organizers",
        "plastic drawer organizer set",
        "makeup drawer organizer",
        "vanity organizer trays",
        "bathroom drawer organizer",
        "kitchen drawer organizer",
        "desk drawer organizer",
        f"{pcs} piece clear plastic drawer organizer with non slip pads",
        f"{n_sizes} sizes nestable drawer bins for makeup kitchen office",
        "modular cabinet drawer storage trays",
    ]

    listing = {
        "market": MARKET,
        "locale": "en_US",
        "brand": brand,
        "title": title,
        "bullets": bullets,
        "highlights": bullets,
        "description": description,
        "item_highlights": item_highlights,
        "backend_search_terms": backend,
        "keywords": keywords,
        "keyword_library": {"primary": keywords[:8], "long_tail": keywords[8:]},
    }
    rules = load_rules()
    listing["compliance"] = gate_listing(listing, MARKET, rules)
    return listing
