"""Render T1-aligned Listing Pack Markdown from pack dict."""
from __future__ import annotations

from typing import Any


def _bullets_md(bullets: list[str]) -> str:
    lines = []
    for i, b in enumerate(bullets, 1):
        lines.append(f"{i}. {b}")
    return "\n".join(lines)


def _sizes_table(sizes: list[dict[str, Any]] | None) -> str:
    if not sizes:
        return "_No sizes in SKU._"
    rows = [
        "| Label | Qty | in (L×W×H) | cm approx |",
        "| --- | --- | --- | --- |",
    ]
    for s in sizes:
        d = s.get("dims_in") or {}
        c = s.get("dims_cm_approx") or {}
        rows.append(
            f"| {s.get('label')} | {s.get('qty')} | "
            f"{d.get('l')}×{d.get('w')}×{d.get('h')} | "
            f"{c.get('l')}×{c.get('w')}×{c.get('h')} |"
        )
    return "\n".join(rows)


def _kw_table(primary: dict[str, list[str]], long_tail: dict[str, list[str]]) -> str:
    lines = [
        "### Primary keywords",
        "| Lang | Terms |",
        "| --- | --- |",
    ]
    for lang, terms in primary.items():
        lines.append(f"| {lang} | {', '.join(terms)} |")
    lines += [
        "",
        "### Long-tail",
        "| Lang | Terms |",
        "| --- | --- |",
    ]
    for lang, terms in long_tail.items():
        lines.append(f"| {lang} | {', '.join(terms)} |")
    return "\n".join(lines)


def render_listing_pack_md(pack: dict[str, Any]) -> str:
    sku = pack.get("sku") or {}
    markets = pack.get("markets") or {}
    am = markets.get("amazon_us") or {}
    sh = markets.get("shopee_id") or {}
    mx = markets.get("meli_mx") or {}
    lib = pack.get("keyword_library") or {}
    compliance = pack.get("compliance") or {}
    listable = pack.get("listable")
    hr = pack.get("human_review_required") or []

    parts: list[str] = []
    parts.append("# T1 Listing Pack (pipeline) — Modular Home Storage (Drawer Organizer)")
    parts.append("")
    parts.append(f"**Generated:** {pack.get('generated_at')} ({pack.get('timezone')})")
    parts.append(f"**Source fixture:** `{pack.get('source_fixture')}`")
    parts.append(f"**listable:** `{listable}`")
    parts.append(f"**Pack version:** {pack.get('pack_version')}")
    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append("## 0) SKU summary")
    parts.append("")
    parts.append("| Field | Value |")
    parts.append("| --- | --- |")
    parts.append(f"| Brand | {sku.get('brand')} |")
    parts.append(f"| Product name (EN) | {sku.get('product_name_en')} |")
    parts.append(f"| Piece count | {sku.get('piece_count')} |")
    parts.append(f"| Pad count | {sku.get('pad_count')} ({sku.get('pad_material')}) |")
    parts.append(f"| Material | {sku.get('material')} |")
    parts.append(f"| Color | {sku.get('color')} |")
    parts.append(f"| Care | {sku.get('care')} |")
    scenes = sku.get("scenes") or []
    parts.append(f"| Scenes | {'; '.join(scenes)} |")
    certs = sku.get("certifications_claimed") or []
    parts.append(f"| Certifications claimed | {certs if certs else '**None claimed**'} |")
    parts.append("")
    parts.append("### Sizes")
    parts.append("")
    parts.append(_sizes_table(sku.get("sizes")))
    parts.append("")
    parts.append("---")
    parts.append("")

    # Amazon
    parts.append("## A) Amazon US (EN)")
    parts.append("")
    parts.append("### Title")
    parts.append("```")
    parts.append(am.get("title") or "")
    parts.append("```")
    parts.append(f"Character count: **{len(am.get('title') or '')}**.")
    parts.append("")
    parts.append("### Bullets")
    parts.append(_bullets_md(list(am.get("bullets") or [])))
    parts.append("")
    parts.append("### Product description")
    parts.append(am.get("description") or "")
    parts.append("")
    if am.get("item_highlights"):
        parts.append("### Item highlights (adapter ≤125)")
        parts.append(am["item_highlights"])
        parts.append("")
    if am.get("backend_search_terms"):
        parts.append("### Backend search terms")
        parts.append("```")
        parts.append(am["backend_search_terms"])
        parts.append("```")
        parts.append(
            f"**Byte estimate (UTF-8):** {len(am['backend_search_terms'].encode('utf-8'))}."
        )
        parts.append("")
    parts.append("---")
    parts.append("")

    # Shopee
    parts.append("## B) Shopee Indonesia (ID)")
    parts.append("")
    parts.append("### Judul (title)")
    parts.append("```")
    parts.append(sh.get("title") or "")
    parts.append("```")
    parts.append("")
    parts.append("### Poin fitur (bullets)")
    parts.append(_bullets_md(list(sh.get("bullets") or [])))
    parts.append("")
    parts.append("### Deskripsi singkat")
    parts.append(sh.get("description") or "")
    parts.append("")
    parts.append("---")
    parts.append("")

    # MELI
    parts.append("## C) Mercado Libre MX (ES)")
    parts.append("")
    parts.append("### Título")
    parts.append("```")
    parts.append(mx.get("title") or "")
    parts.append("```")
    parts.append("")
    parts.append("### Viñetas")
    parts.append(_bullets_md(list(mx.get("bullets") or [])))
    parts.append("")
    parts.append("### Descripción corta")
    parts.append(mx.get("description") or "")
    parts.append("")
    parts.append("---")
    parts.append("")

    # Keywords
    parts.append("## D) Category keyword library")
    parts.append("")
    parts.append(
        _kw_table(lib.get("primary") or {}, lib.get("long_tail") or {})
    )
    parts.append("")
    parts.append("### Do-not-translate / keep-as-is")
    for tok in lib.get("do_not_translate") or []:
        parts.append(f"- {tok}")
    parts.append("")
    parts.append("### Site-specific notes")
    parts.append("| Site | Notes |")
    parts.append("| --- | --- |")
    for site, note in (lib.get("site_notes") or {}).items():
        parts.append(f"| {site} | {note} |")
    parts.append("")
    parts.append("---")
    parts.append("")

    # Compliance
    parts.append("## E) Compliance gate checks")
    parts.append("")
    parts.append(f"**Overall listable:** `{listable}`")
    parts.append(f"**all_pass:** `{compliance.get('all_pass')}`")
    parts.append("")
    parts.append("| Market | Pass | Title length | Reasons |")
    parts.append("| --- | --- | --- | --- |")
    for mkey, row in (compliance.get("markets") or {}).items():
        reasons = "; ".join(row.get("reasons") or []) or "—"
        parts.append(
            f"| {mkey} | {row.get('pass')} | {row.get('title_length')} | {reasons} |"
        )
    parts.append("")
    if compliance.get("fail_reasons"):
        parts.append("### Fail reasons")
        for r in compliance["fail_reasons"]:
            parts.append(f"- {r}")
        parts.append("")

    parts.append("### Human review (polish vs hand T1 — does not flip listable)")
    if not hr:
        parts.append("_None._")
    else:
        for note in hr:
            parts.append(
                f"- **{note.get('marketplace')} / {note.get('field')}**: "
                f"{note.get('detail')}"
            )
    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append("## Pack inventory")
    parts.append("")
    parts.append("- Amazon US: title, bullets, description, item highlights, backend terms")
    parts.append("- Shopee ID: title, bullets, description, keywords")
    parts.append("- MELI MX: title, bullets, description, keywords")
    parts.append("- Keyword library + compliance + listable flag")
    parts.append("")
    return "\n".join(parts) + "\n"
