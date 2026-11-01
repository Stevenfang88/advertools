"""Shopee Philippines listing adapter — English PH, title 25–100, keyword library."""
from __future__ import annotations

from typing import Any

from .compliance_gate import gate_listing, load_rules

MARKET = "shopee_ph"

REQUIRED_KEYWORDS = ("drawer organizer", "drawer divider")


def _cm_line(sku: dict[str, Any]) -> str:
    parts = []
    for s in sku.get("sizes") or []:
        d = s.get("dims_cm_approx") or {}
        lab = s.get("label")
        if d:
            parts.append(
                f"{s.get('qty')} pcs {lab} (~{d.get('l'):.0f}x{d.get('w'):.0f}x{d.get('h'):.0f} cm)"
            )
        else:
            parts.append(f"{s.get('qty')} pcs {lab}")
    return "; ".join(parts)


def generate(sku: dict[str, Any]) -> dict[str, Any]:
    pcs = sku.get("piece_count", 0)
    pads = sku.get("pad_count", 0)
    n_sizes = len(sku.get("sizes") or [])
    brand = sku.get("brand") or ""

    # English PH title — not ALL-CAPS; no promo spam (sale / free shipping / best seller)
    title = (
        f"Drawer Organizer {pcs} Pcs Clear Plastic {n_sizes} Sizes Non-Slip Pads"
    )
    if len(title) < 25:
        title = f"Clear Plastic Drawer Organizer Set {pcs} Pcs {n_sizes} Sizes"
    if len(title) > 100:
        title = title[:100].rstrip()

    cm = _cm_line(sku)
    bullets = [
        (
            f"{pcs} pcs in {n_sizes} sizes — {cm}; mix layouts to fit your drawer."
        ),
        (
            "Clear plastic — Spot makeup, jewelry, kitchen tools, or office supplies at a glance."
        ),
        (
            f"{pads} silicone non-slip pads — Stick on tray corners to reduce sliding when "
            f"you open or close the drawer."
        ),
        (
            "Modular and nestable — Arrange side by side; nest unused trays to save space."
        ),
        (
            "Easy to clean — Wipe with a damp cloth or hand-rinse with water."
        ),
        (
            "Multi-scene use — Makeup vanity, under-sink, kitchen utensils, and desk drawers."
        ),
    ]

    description = (
        f"Tidy messy drawers with this {pcs}-piece clear plastic drawer organizer set. "
        f"{n_sizes} sizes help you sort makeup, bathroom items, kitchen gadgets, and "
        f"desk supplies. Includes silicone non-slip pads. Modular layout in the drawer; "
        f"nest empty trays when not in use. Wipe clean or hand-rinse. For everyday home "
        f"organization only."
    )
    if len(description) < 100:
        description += " Clear durable PET plastic for household use."

    keywords = [
        "drawer organizer",
        "drawer divider",
        "clear drawer organizer",
        "plastic drawer organizer set",
        "makeup drawer organizer",
        "kitchen drawer organizer",
        f"{pcs} pcs clear drawer organizer {n_sizes} sizes non slip",
        "drawer divider trays for vanity bathroom kitchen",
        "nestable modular drawer storage bins",
    ]
    for req in REQUIRED_KEYWORDS:
        if req not in keywords:
            keywords.insert(0, req)

    listing = {
        "market": MARKET,
        "locale": "en_PH",
        "brand": brand,
        "title": title,
        "bullets": bullets,
        "highlights": bullets,
        "description": description,
        "keywords": keywords,
        "keyword_library": {
            "primary": [
                "drawer organizer",
                "drawer divider",
                "clear drawer organizer",
                "plastic drawer organizer set",
                "makeup drawer organizer",
                "kitchen drawer organizer",
            ],
            "long_tail": keywords[6:],
        },
    }
    rules = load_rules()
    listing["compliance"] = gate_listing(listing, MARKET, rules)
    return listing
