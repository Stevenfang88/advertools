"""Mercado Libre Brazil (PT) listing adapter — title ≤60, no punctuation, Portuguese-first."""
from __future__ import annotations

from typing import Any

from .compliance_gate import gate_listing, load_rules

MARKET = "meli_br"


def _cm_line(sku: dict[str, Any]) -> str:
    parts = []
    label_pt = {
        "large": "grandes",
        "medium_long": "alongadas",
        "medium": "medias",
        "small": "pequenas",
    }
    for s in sku.get("sizes") or []:
        d = s.get("dims_cm_approx") or {}
        lab = label_pt.get(s.get("label"), s.get("label"))
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

    # Portuguese nouns first; spaces only; no punctuation; no EN product nouns
    title = f"Organizador gavetas plastico transparente {pcs} pcs {n_sizes} tamanhos"
    if len(title) > 60:
        title = f"Organizador gavetas plastico {pcs} pcs {n_sizes} tamanhos"
    title = title[:60].rstrip()

    cm = _cm_line(sku)
    bullets = [
        (
            f"{pcs} bandejas em {n_sizes} tamanhos — {cm} para montar o layout da gaveta."
        ),
        (
            "Plastico transparente — Ve cosmeticos, utensilios, joias ou material de "
            "escritorio de relance."
        ),
        (
            f"{pads} almofadas de silicone antiderrapantes — Colam nos cantos para "
            f"reduzir o deslizamento ao abrir ou fechar a gaveta."
        ),
        (
            "Modular e empilhavel — Combine na gaveta; guarde as que nao usa "
            "empilhadas para economizar espaco."
        ),
        (
            "Cuidado simples — Limpe com pano umido ou enxague com a mao."
        ),
        (
            "Cenas de uso — Gaveta de maquiagem, sob a pia, utensilios de cozinha, "
            "escrivaninha."
        ),
    ]

    description = (
        f"Organize gavetas com um conjunto de {pcs} bandejas transparentes em "
        f"{n_sizes} tamanhos. Ideal para maquiagem, banheiro, cozinha e escritorio. "
        f"Inclui almofadas antiderrapantes. Limpeza com pano umido ou enxague manual. "
        f"Uso domestico de organizacao — sem alegacoes medicas ou de seguranca infantil."
    )

    keywords = [
        "organizador de gavetas",
        "organizadores de plastico transparente",
        "kit organizador gaveta",
        "organizador maquiagem",
        "organizador cozinha",
        "separadores de gavetas",
        f"kit {pcs} organizadores gavetas {n_sizes} tamanhos antiderrapante",
        "organizador gaveta sob a pia",
        "bandejas transparentes maquiagem cozinha escritorio",
    ]

    listing = {
        "market": MARKET,
        "locale": "pt_BR",
        "brand": brand,
        "title": title,
        "bullets": bullets,
        "highlights": bullets,
        "description": description,
        "keywords": keywords,
        "keyword_library": {"primary": keywords[:6], "long_tail": keywords[6:]},
    }
    rules = load_rules()
    listing["compliance"] = gate_listing(listing, MARKET, rules)
    return listing
