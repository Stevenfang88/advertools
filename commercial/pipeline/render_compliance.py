"""Short compliance report Markdown."""
from __future__ import annotations

from typing import Any


def render_compliance_md(pack: dict[str, Any]) -> str:
    compliance = pack.get("compliance") or {}
    listable = pack.get("listable")
    lines = [
        "# Listing Pack — Compliance Report",
        "",
        f"**Generated:** {pack.get('generated_at')} ({pack.get('timezone')})",
        f"**Source:** `{pack.get('source_fixture')}`",
        f"**listable:** `{listable}`",
        f"**all_pass:** `{compliance.get('all_pass')}`",
        "",
        "## Per-market gate",
        "",
        "| Market | Pass | Title length | Reasons |",
        "| --- | --- | --- | --- |",
    ]
    for mkey, row in (compliance.get("markets") or {}).items():
        reasons = "; ".join(row.get("reasons") or []) or "—"
        lines.append(
            f"| {mkey} | {row.get('pass')} | {row.get('title_length')} | {reasons} |"
        )
    lines.append("")
    lines.append("## Checklist")
    lines.append("")
    for item in compliance.get("checklist") or []:
        check = item.get("check", "?")
        if "amazon_us" in item:
            lines.append(
                f"- **{check}**: amazon={item.get('amazon_us')} "
                f"shopee={item.get('shopee_id')} meli={item.get('meli_mx')}"
            )
        else:
            result = item.get("result")
            notes = item.get("notes")
            extra = f" — {notes}" if notes else ""
            lines.append(f"- **{check}**: {result}{extra}")
    lines.append("")
    if compliance.get("fail_reasons"):
        lines.append("## Fail reasons (blocks listable)")
        lines.append("")
        for r in compliance["fail_reasons"]:
            lines.append(f"- {r}")
        lines.append("")
    else:
        lines.append("## Fail reasons")
        lines.append("")
        lines.append("_None — compliance gate passed for all markets._")
        lines.append("")

    hr = pack.get("human_review_required") or []
    lines.append("## Human review required (polish; does not block listable)")
    lines.append("")
    if not hr:
        lines.append("_None._")
    else:
        for note in hr:
            lines.append(
                f"- **{note.get('marketplace')} / {note.get('field')}** "
                f"[{note.get('severity')}]: {note.get('detail')}"
            )
    lines.append("")
    auto = (pack.get("auto_vs_manual") or {}).get("auto") or []
    polish = (pack.get("auto_vs_manual") or {}).get("human_polish") or []
    lines.append("## Auto vs human polish")
    lines.append("")
    lines.append("**Auto (from adapters):**")
    for a in auto:
        lines.append(f"- {a}")
    lines.append("")
    lines.append("**Flagged for human polish:**")
    for p in polish:
        lines.append(f"- {p}")
    lines.append("")
    return "\n".join(lines)
