"""Shopee Indonesia listing adapter — Bahasa ID, title 25–100, keyword library.

``keywords`` / ``keyword_library`` come from :func:`adapters.keyword_engine.build_keywords`.
Required stems ``organizer laci`` and ``sekat laci`` are pinned there, then the
listing is scored by :func:`adapters.compliance_gate.gate_listing`. Title and
bullets are not produced by that path.
"""
from __future__ import annotations

from typing import Any

from .compliance_gate import gate_listing, load_rules
from .keyword_engine import SHOPEE_ID_REQUIRED_KEYWORDS, build_keywords

MARKET = "shopee_id"

REQUIRED_KEYWORDS = SHOPEE_ID_REQUIRED_KEYWORDS


def _cm_line(sku: dict[str, Any]) -> str:
    parts = []
    label_id = {
        "large": "besar",
        "medium_long": "panjang",
        "medium": "sedang",
        "small": "kecil",
    }
    for s in sku.get("sizes") or []:
        d = s.get("dims_cm_approx") or {}
        lab = label_id.get(s.get("label"), s.get("label"))
        if d:
            parts.append(
                f"{s.get('qty')} pcs {lab} (~{d.get('l'):.0f}×{d.get('w'):.0f}×{d.get('h'):.0f} cm)"
            )
        else:
            parts.append(f"{s.get('qty')} pcs {lab}")
    return "; ".join(parts)


def generate(sku: dict[str, Any]) -> dict[str, Any]:
    pcs = sku.get("piece_count", 0)
    pads = sku.get("pad_count", 0)
    n_sizes = len(sku.get("sizes") or [])
    brand = sku.get("brand") or ""

    # Bahasa title — category + spec + scene; not ALL-CAPS; no promo spam
    # Target style near sample_titles shopee_id_fixed (25–100)
    title = (
        f"Organizer Laci {pcs} Pcs Plastik Bening {n_sizes} Ukuran "
        f"Anti Slip Makeup Dapur"
    )
    if len(title) < 25:
        title = f"Set Organizer Laci {pcs} Pcs Plastik Bening {n_sizes} Ukuran Anti Slip"
    if len(title) > 100:
        title = title[:100].rstrip()

    cm = _cm_line(sku)
    bullets = [
        (
            f"Isi {pcs} pcs, {n_sizes} ukuran — {cm}; bisa digabung sesuai isi laci."
        ),
        (
            "Plastik bening — Isi terlihat jelas: kosmetik, perhiasan, peralatan dapur, ATK."
        ),
        (
            f"{pads} bantalan silikon anti slip — Tempel di sudut wadah agar tidak mudah "
            f"bergeser saat laci dibuka-tutup."
        ),
        (
            "Modular dan bisa disarangkan — Susun di dalam laci; wadah kosong bisa "
            "ditumpuk untuk hemat tempat."
        ),
        (
            "Mudah dibersihkan — Lap dengan kain lembap atau bilas tangan saja."
        ),
        (
            "Hemat ruang — Cocok untuk laci makeup, bawah wastafel, dapur, dan meja kerja."
        ),
    ]

    description = (
        f"Rapikan laci berantakan dengan set organizer plastik bening {pcs} pcs. "
        f"Empat ukuran membantu menata makeup, peralatan dapur, isi kamar mandi, "
        f"dan ATK. Dilengkapi bantalan silikon anti slip. Susun modular di dalam "
        f"laci; wadah cadangan bisa disarangkan. Bersihkan dengan lap lembap atau "
        f"bilas tangan. Untuk organisasi rumah tangga sehari-hari."
    )
    # Ensure ≥100 chars (Shopee description_min)
    if len(description) < 100:
        description += " Bahan plastik PET bening yang tahan dipakai di rumah."

    kw = build_keywords(sku, MARKET)
    # Required stems are pinned inside the engine; keep the local check so a
    # future cut cannot ship a Shopee ID pack without them.
    keywords = list(kw["keywords"])
    for req in REQUIRED_KEYWORDS:
        if req not in keywords:
            keywords.insert(0, req)
    library = kw["keyword_library"]
    primary = list(library.get("primary") or [])
    for req in reversed(REQUIRED_KEYWORDS):
        if req not in primary:
            primary.insert(0, req)

    listing = {
        "market": MARKET,
        "locale": "id_ID",
        "brand": brand,
        "title": title,
        "bullets": bullets,
        "highlights": bullets,
        "description": description,
        "keywords": keywords,
        "keyword_library": {
            "primary": primary,
            "long_tail": list(library.get("long_tail") or []),
        },
        "keyword_generation": kw["keyword_generation"],
    }
    rules = load_rules()
    listing["compliance"] = gate_listing(listing, MARKET, rules)
    return listing
