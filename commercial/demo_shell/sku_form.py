"""Assemble SKU dict from form / API payload; fill gaps from drawer fixture."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "fixtures" / "drawer_organizer_25pcs.json"


def load_default_fixture() -> dict[str, Any]:
    return json.loads(DEFAULT_FIXTURE.read_text(encoding="utf-8"))


def _parse_scenes(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(s).strip() for s in raw if str(s).strip()]
    text = str(raw or "").strip()
    if not text:
        return []
    # comma / Chinese顿号 / newline
    for sep in ["\n", "、", "，", ","]:
        text = text.replace(sep, ",")
    return [p.strip() for p in text.split(",") if p.strip()]


def _parse_sizes(raw: Any, fallback: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if raw is None or raw == "":
        return copy.deepcopy(fallback)
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return copy.deepcopy(fallback)
        return json.loads(raw)
    raise ValueError("sizes must be a JSON array or omitted")


def assemble_sku(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a schema-shaped SKU; missing forbidden_claims / sizes come from fixture."""
    base = load_default_fixture()
    payload = payload or {}

    brand = str(payload.get("brand") if payload.get("brand") is not None else base["brand"]).strip()
    product_name_en = str(
        payload.get("product_name_en")
        if payload.get("product_name_en") is not None
        else base["product_name_en"]
    ).strip()
    material = str(
        payload.get("material") if payload.get("material") is not None else base["material"]
    ).strip()
    care = str(payload.get("care") if payload.get("care") is not None else base["care"]).strip()

    piece_raw = payload.get("piece_count", base["piece_count"])
    piece_count = int(piece_raw)

    scenes = _parse_scenes(payload.get("scenes", base["scenes"]))
    if not scenes:
        scenes = list(base["scenes"])

    sizes = _parse_sizes(payload.get("sizes"), base["sizes"])

    forbidden = payload.get("forbidden_claims")
    if forbidden is None or forbidden == "":
        forbidden = list(base["forbidden_claims"])
    elif isinstance(forbidden, str):
        forbidden = [p.strip() for p in forbidden.replace("\n", ",").split(",") if p.strip()]
    else:
        forbidden = list(forbidden)

    sku: dict[str, Any] = {
        "brand": brand,
        "product_name_en": product_name_en,
        "piece_count": piece_count,
        "sizes": sizes,
        "material": material,
        "care": care,
        "scenes": scenes,
        "forbidden_claims": forbidden,
    }

    # Optional fields
    for key in ("pad_count", "pad_material", "color", "notes"):
        if key in payload and payload[key] not in (None, ""):
            sku[key] = (
                int(payload[key]) if key == "pad_count" else payload[key]
            )
        elif key in base:
            sku[key] = copy.deepcopy(base[key])

    certs = payload.get("certifications_claimed")
    if certs is None:
        sku["certifications_claimed"] = list(base.get("certifications_claimed") or [])
    elif isinstance(certs, str):
        sku["certifications_claimed"] = [
            p.strip() for p in certs.replace("\n", ",").split(",") if p.strip()
        ]
    else:
        sku["certifications_claimed"] = list(certs)

    return sku


def fixture_for_form() -> dict[str, Any]:
    """Flatten fixture into form-friendly defaults."""
    sku = load_default_fixture()
    return {
        "brand": sku["brand"],
        "product_name_en": sku["product_name_en"],
        "piece_count": sku["piece_count"],
        "pad_count": sku.get("pad_count", 0),
        "pad_material": sku.get("pad_material", ""),
        "color": sku.get("color", ""),
        "material": sku["material"],
        "care": sku["care"],
        "scenes": ", ".join(sku["scenes"]),
        "sizes_json": json.dumps(sku["sizes"], ensure_ascii=False, indent=2),
        "forbidden_claims": ", ".join(sku["forbidden_claims"]),
    }
