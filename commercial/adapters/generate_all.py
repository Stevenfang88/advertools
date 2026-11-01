"""Orchestrator: SKU JSON → multi-market packs + compliance gates."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import amazon_en, meli_ar, meli_br, meli_mx, shopee_id, shopee_ph, shopee_th

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "fixtures" / "drawer_organizer_25pcs.json"
DEFAULT_OUT = ROOT / "fixtures" / "drawer_organizer_25pcs.generated.json"

# Stable order: original three, then SEA/LatAm extensions
MARKET_GENERATORS = (
    ("amazon_us", amazon_en.generate),
    ("shopee_id", shopee_id.generate),
    ("meli_mx", meli_mx.generate),
    ("shopee_th", shopee_th.generate),
    ("shopee_ph", shopee_ph.generate),
    ("meli_br", meli_br.generate),
    ("meli_ar", meli_ar.generate),
)


def load_sku(path: Path | str) -> dict[str, Any]:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8"))


def generate_all(sku: dict[str, Any]) -> dict[str, Any]:
    packs = {key: gen(sku) for key, gen in MARKET_GENERATORS}
    all_pass = all(p.get("compliance", {}).get("pass") for p in packs.values())
    return {
        "sku_brand": sku.get("brand"),
        "sku_product_name_en": sku.get("product_name_en"),
        "markets": packs,
        "all_compliance_pass": all_pass,
    }


def generate_from_path(
    fixture: Path | str | None = None,
    out: Path | str | None = None,
    write: bool = True,
) -> dict[str, Any]:
    fixture_path = Path(fixture) if fixture else DEFAULT_FIXTURE
    out_path = Path(out) if out else DEFAULT_OUT
    sku = load_sku(fixture_path)
    result = generate_all(sku)
    result["source_fixture"] = str(fixture_path)
    if write:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        result["output_path"] = str(out_path)
    return result
