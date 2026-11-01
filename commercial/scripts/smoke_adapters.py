#!/usr/bin/env python3
"""Smoke tests for Step 1 adapters against the drawer golden fixture."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters.generate_all import generate_from_path  # noqa: E402
from adapters.shopee_id import REQUIRED_KEYWORDS as SHOPEE_ID_KW  # noqa: E402
from adapters.shopee_ph import REQUIRED_KEYWORDS as SHOPEE_PH_KW  # noqa: E402
from adapters.shopee_th import REQUIRED_KEYWORDS as SHOPEE_TH_KW  # noqa: E402

EXPECTED_MARKETS = (
    "amazon_us",
    "shopee_id",
    "meli_mx",
    "shopee_th",
    "shopee_ph",
    "meli_br",
    "meli_ar",
)


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"PASS: {msg}")


def _assert_shopee(name: str, pack: dict, required_kw: tuple[str, ...], promos: tuple[str, ...]) -> None:
    t = pack["title"]
    if not (25 <= len(t) <= 100):
        fail(f"{name} title len {len(t)} not in 25–100")
    ok(f"{name} title len={len(t)}")
    letters = [c for c in t if c.isalpha()]
    if letters and sum(1 for c in letters if c.isupper()) / len(letters) >= 0.85:
        fail(f"{name} title ALL-CAPS")
    for promo in promos:
        if promo.lower() in t.lower():
            fail(f"{name} promo word: {promo}")
    ok(f"{name} no ALL-CAPS / promo spam")
    kw_text = " ".join(pack.get("keywords") or [])
    # casefold for Latin; keep Thai exact
    kw_fold = kw_text.casefold()
    for req in required_kw:
        if req.casefold() not in kw_fold and req not in kw_text:
            fail(f"{name} keywords missing {req!r}")
    ok(f"{name} keywords include required stems")


def _assert_meli(name: str, pack: dict) -> None:
    mt = pack["title"]
    if len(mt) > 60:
        fail(f"{name} title len {len(mt)} >60")
    ok(f"{name} title len={len(mt)}")
    if re.search(r"[^\w\s]", mt, flags=re.UNICODE):
        fail(f"{name} title has punctuation")
    ok(f"{name} title no punctuation")
    if re.search(
        r"(?i)\b(drawer|organizer|makeup|vanity|bathroom|kitchen|office|desk|"
        r"storage|bins|trays|pads|non[- ]?slip|clear|plastic|set|piece|pieces)\b",
        mt,
    ):
        fail(f"{name} English product word in title: {mt!r}")
    ok(f"{name} no EN product nouns in title")


def main() -> None:
    result = generate_from_path(write=True)
    markets = result["markets"]

    for key in EXPECTED_MARKETS:
        if key not in markets:
            fail(f"missing market pack: {key}")
    ok(f"All {len(EXPECTED_MARKETS)} markets present")

    am = markets["amazon_us"]
    # Amazon
    if len(am["title"]) > 75:
        fail(f"Amazon title len {len(am['title'])} > 75")
    ok(f"Amazon title len={len(am['title'])} ≤75")
    if len(am["bullets"]) != 5:
        fail(f"Amazon bullets count {len(am['bullets'])}")
    for i, b in enumerate(am["bullets"]):
        if not (10 <= len(b) <= 255):
            fail(f"Amazon bullet[{i}] len={len(b)}")
    ok("Amazon 5 bullets in 10–255")
    be = am["backend_search_terms"]
    if len(be.encode("utf-8")) > 249:
        fail("Amazon backend >249 bytes")
    ok(f"Amazon backend bytes={len(be.encode('utf-8'))}")
    ih = am.get("item_highlights") or ""
    if ih and len(ih) > 125:
        fail(f"item_highlights {len(ih)} >125")
    ok(f"Amazon item_highlights len={len(ih)}")

    _assert_shopee(
        "Shopee ID",
        markets["shopee_id"],
        SHOPEE_ID_KW,
        ("diskon", "gratis ongkir", "best seller", "hot item"),
    )
    _assert_shopee(
        "Shopee TH",
        markets["shopee_th"],
        SHOPEE_TH_KW,
        ("ลดแรง", "free shipping", "best seller", "hot item", "flash sale"),
    )
    _assert_shopee(
        "Shopee PH",
        markets["shopee_ph"],
        SHOPEE_PH_KW,
        ("sale", "free shipping", "best seller", "hot item"),
    )

    _assert_meli("MELI MX", markets["meli_mx"])
    _assert_meli("MELI BR", markets["meli_br"])
    _assert_meli("MELI AR", markets["meli_ar"])

    # Banned claims across all generated string fields
    banned = [
        re.compile(r"(?i)100%\s*BPA[- ]?FREE"),
        re.compile(r"(?i)dishwasher[- ]?safe"),
        re.compile(r"(?i)unbreakable|indestructible"),
        re.compile(r"(?i)trusted by thousands|#\s*1\s*bestseller"),
        re.compile(r"(?i)childproof|baby[- ]?safe"),
    ]

    def walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "compliance":
                    continue
                yield from walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                yield from walk(v, f"{path}[{i}]")
        elif isinstance(obj, str):
            yield path, obj

    for path, text in walk(markets):
        for pat in banned:
            if pat.search(text):
                fail(f"banned claim at {path}: {pat.pattern}")
    ok("No banned claims in generated fields")

    # Coherent non-empty copy
    for name, pack in markets.items():
        if not (pack.get("title") and pack.get("description") and pack.get("bullets")):
            fail(f"{name} missing title/description/bullets")
        if "25" not in pack["title"] and "25" not in (pack.get("description") or ""):
            fail(f"{name} missing piece_count signal")
    ok("Non-empty coherent copy with piece_count")

    if not result.get("all_compliance_pass"):
        for k, p in markets.items():
            c = p.get("compliance") or {}
            if not c.get("pass"):
                print(k, c.get("reasons"))
        fail("gate reported FAIL")
    ok(f"All {len(markets)} markets compliance PASS")
    print(f"\nSMOKE_OK output={result.get('output_path')}")
    print("titles:")
    for k in EXPECTED_MARKETS:
        p = markets[k]
        print(f"  {k}: ({len(p['title'])}) {p['title']}")


if __name__ == "__main__":
    main()
