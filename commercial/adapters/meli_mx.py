"""Mercado Libre Mexico (ES) listing adapter — title ≤60, no punctuation, Spanish-first.

``keywords`` / ``keyword_library`` come from :func:`adapters.keyword_engine.build_keywords`
(advertools ``word_frequency``, ``kw_generate``, ``ad_from_string``), then the
whole listing is scored by :func:`adapters.compliance_gate.gate_listing`.
Title and bullets are not produced by that path.
"""
from __future__ import annotations

from typing import Any

from .compliance_gate import gate_listing, load_rules
from .keyword_engine import build_keywords

MARKET = "meli_mx"


def _cm_line(sku: dict[str, Any]) -> str:
    parts = []
    label_es = {
        "large": "grandes",
        "medium_long": "alargadas",
        "medium": "medianas",
        "small": "pequenas",
    }
    for s in sku.get("sizes") or []:
        d = s.get("dims_cm_approx") or {}
        lab = label_es.get(s.get("label"), s.get("label"))
        if d:
            parts.append(
                f"{s.get('qty')} {lab} (~{d.get('l'):.0f}x{d.get('w'):.0f}x{d.get('h'):.0f} cm)"
            )
        else:
            parts.append(f"{s.get('qty')} {lab}")
    return ", ".join(parts)


def generate(sku: dict[str, Any]) -> dict[str, Any]:
    pcs = sku.get("piece_count", 0)
    pads = sku.get("pad_count", 0)
    n_sizes = len(sku.get("sizes") or [])
    brand = sku.get("brand") or ""

    # Spanish nouns first; spaces only; no punctuation/symbols; no Spanglish EN nouns
    # Accent-free ASCII style matches sample_titles meli_mx_fixed (marketplace-safe)
    title = f"Organizador cajones plastico transparente {pcs} pzs {n_sizes} tamanos"
    if len(title) > 60:
        title = f"Organizador cajones plastico {pcs} pzs {n_sizes} tamanos"
    title = title[:60].rstrip()

    cm = _cm_line(sku)
    bullets = [
        (
            f"{pcs} bandejas en {n_sizes} tamanos — {cm} para armar el layout del cajon."
        ),
        (
            "Plastico transparente — Ves cosmeticos, utensilios, joyas o utiles de "
            "oficina de un vistazo."
        ),
        (
            f"{pads} almohadillas de silicona antideslizantes — Se pegan en las "
            f"esquinas para reducir el deslizamiento al abrir o cerrar el cajon."
        ),
        (
            "Modular y anidable — Combinalas en el cajon; guarda las que no uses "
            "anidadas para ahorrar espacio."
        ),
        (
            "Cuidado sencillo — Limpia con un pano humedo o enjuaga a mano."
        ),
        (
            "Escenas de uso — Cajon de maquillaje, debajo del fregadero, utensilios "
            "de cocina, escritorio."
        ),
    ]

    description = (
        f"Organiza cajones con un set de {pcs} bandejas transparentes en "
        f"{n_sizes} tamanos. Ideal para maquillaje, bano, cocina y oficina. "
        f"Incluye almohadillas antideslizantes. Limpieza con pano humedo o "
        f"enjuague a mano. Uso domestico de organizacion — sin afirmaciones "
        f"medicas ni de seguridad infantil."
    )

    kw = build_keywords(sku, MARKET)

    listing = {
        "market": MARKET,
        "locale": "es_MX",
        "brand": brand,
        "title": title,
        "bullets": bullets,
        "highlights": bullets,
        "description": description,
        "keywords": kw["keywords"],
        "keyword_library": kw["keyword_library"],
        "keyword_generation": kw["keyword_generation"],
    }
    rules = load_rules()
    listing["compliance"] = gate_listing(listing, MARKET, rules)
    return listing
