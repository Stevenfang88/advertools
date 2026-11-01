"""Assemble Listing Pack JSON + overall listable gate."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from adapters.generate_all import generate_all, load_sku

from .compare_t1 import compare_to_t1
from .render_compliance import render_compliance_md
from .render_md import render_listing_pack_md

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SKU = ROOT / "fixtures" / "drawer_organizer_25pcs.json"
DEFAULT_OUT_DIR = Path(__file__).resolve().parent / "out"
DEFAULT_T1 = Path("/workspace/T1-Listing-Pack-v0-drawer-organizer.md")
SHANGHAI = ZoneInfo("Asia/Shanghai")


def _sku_slug(sku: dict[str, Any]) -> str:
    name = (sku.get("product_name_en") or "sku").lower()
    pcs = sku.get("piece_count")
    slug = "".join(c if c.isalnum() else "_" for c in name)
    slug = "_".join(p for p in slug.split("_") if p)[:48]
    if pcs:
        return f"{slug}_{pcs}pcs"
    return slug or "listing_pack"


def _merged_keyword_library(markets: dict[str, Any]) -> dict[str, Any]:
    """Merge per-market keyword_library into T1-style EN / ID / ES tables."""
    lang_map = {
        "amazon_us": "EN",
        "shopee_id": "ID",
        "meli_mx": "ES_MX",
    }
    primary: dict[str, list[str]] = {}
    long_tail: dict[str, list[str]] = {}
    for key, lang in lang_map.items():
        lib = (markets.get(key) or {}).get("keyword_library") or {}
        primary[lang] = list(lib.get("primary") or [])
        long_tail[lang] = list(lib.get("long_tail") or [])
    return {
        "primary": primary,
        "long_tail": long_tail,
        "do_not_translate": [
            "OK Home Organizer",
            "PET",
            "pcs / PCS",
            "Non-Slip / Anti Slip (EN feature token)",
            "SKU / ASIN / MLM codes",
        ],
        "site_notes": {
            "amazon_us": (
                "Front-load piece count + clear plastic + drawer organizer; "
                "backend terms complementary; no competitor brands."
            ),
            "shopee_id": (
                "Bahasa title; mix organizer laci + sekat laci + pcs + bening; "
                "no ALL-CAPS spam."
            ),
            "meli_mx": (
                "Spanish nouns first; no Spanglish in title; no punctuation; "
                "price/shipping stay out of title."
            ),
        },
    }


def build_compliance_summary(markets: dict[str, Any]) -> dict[str, Any]:
    per_market: dict[str, Any] = {}
    all_reasons: list[str] = []
    for key, pack in markets.items():
        comp = pack.get("compliance") or {}
        passed = bool(comp.get("pass"))
        reasons = list(comp.get("reasons") or [])
        per_market[key] = {
            "pass": passed,
            "title_pass": (comp.get("title") or {}).get("pass"),
            "title_length": (comp.get("title") or {}).get("length"),
            "reasons": reasons,
        }
        for r in reasons:
            all_reasons.append(f"{key}: {r}")
    all_pass = all(v["pass"] for v in per_market.values()) if per_market else False
    return {
        "all_pass": all_pass,
        "markets": per_market,
        "fail_reasons": all_reasons,
        "checklist": [
            {
                "check": "title_length_and_style",
                "amazon_us": per_market.get("amazon_us", {}).get("pass"),
                "shopee_id": per_market.get("shopee_id", {}).get("pass"),
                "meli_mx": per_market.get("meli_mx", {}).get("pass"),
            },
            {
                "check": "banned_claims_absent",
                "result": all_pass,
                "notes": "Scored by adapters.compliance_gate against rules/compliance.yaml",
            },
            {
                "check": "piece_count_present_in_title_or_body",
                "result": all(
                    "25" in ((p.get("title") or "") + (p.get("description") or ""))
                    for p in markets.values()
                ),
            },
        ],
    }


def build_pack(
    sku: dict[str, Any],
    *,
    source_fixture: str | None = None,
    t1_path: Path | str | None = DEFAULT_T1,
) -> dict[str, Any]:
    generated = generate_all(sku)
    markets = generated["markets"]
    compliance = build_compliance_summary(markets)
    listable = bool(compliance["all_pass"])
    human_review = compare_to_t1(markets, t1_path=t1_path)
    now = datetime.now(SHANGHAI).isoformat(timespec="seconds")

    pack: dict[str, Any] = {
        "pack_version": "T1-aligned-v0-pipeline",
        "generated_at": now,
        "timezone": "Asia/Shanghai",
        "source_fixture": source_fixture,
        "sku": {
            "brand": sku.get("brand"),
            "product_name_en": sku.get("product_name_en"),
            "piece_count": sku.get("piece_count"),
            "pad_count": sku.get("pad_count"),
            "sizes": sku.get("sizes"),
            "material": sku.get("material"),
            "pad_material": sku.get("pad_material"),
            "color": sku.get("color"),
            "care": sku.get("care"),
            "scenes": sku.get("scenes"),
            "certifications_claimed": sku.get("certifications_claimed") or [],
        },
        "markets": markets,
        "keyword_library": _merged_keyword_library(markets),
        "compliance": compliance,
        "listable": listable,
        "human_review_required": human_review,
        "auto_vs_manual": {
            "auto": [
                "titles",
                "bullets",
                "descriptions",
                "amazon backend_search_terms / item_highlights",
                "per-market keyword_library",
                "compliance gate scores",
            ],
            "human_polish": [
                "Match longer T1 Amazon title / A+ paragraph if desired",
                "Scene wording / soften phrasing vs hand pack",
                "Photo shot list and attribute form maps (out of scope Step 2)",
            ],
        },
    }
    return pack


def export_pack(
    sku_path: Path | str,
    out_dir: Path | str | None = None,
    *,
    t1_path: Path | str | None = DEFAULT_T1,
) -> dict[str, Any]:
    """Load SKU, build pack, write MD + JSON + compliance report. Returns meta."""
    sku_path = Path(sku_path)
    out_dir = Path(out_dir) if out_dir else DEFAULT_OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    sku = load_sku(sku_path)
    pack = build_pack(sku, source_fixture=str(sku_path.resolve()), t1_path=t1_path)
    slug = _sku_slug(sku)
    stem = f"{slug}_listing_pack"

    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"
    compliance_path = out_dir / f"{stem}-compliance.md"

    json_path.write_text(
        json.dumps(pack, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(render_listing_pack_md(pack), encoding="utf-8")
    compliance_path.write_text(render_compliance_md(pack), encoding="utf-8")

    return {
        "listable": pack["listable"],
        "slug": slug,
        "out_dir": str(out_dir.resolve()),
        "json_path": str(json_path.resolve()),
        "md_path": str(md_path.resolve()),
        "compliance_path": str(compliance_path.resolve()),
        "titles": {k: (v.get("title") or "") for k, v in pack["markets"].items()},
        "human_review_count": len(pack.get("human_review_required") or []),
        "pack": pack,
    }
