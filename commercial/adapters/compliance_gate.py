"""Compliance gate for multi-market listing copy.

Loads commercial/rules/compliance.yaml and scores titles + body fields.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULES = ROOT / "rules" / "compliance.yaml"

# English product-ish tokens that look like Spanglish/Portuglish when stuffed into MELI titles.
_MELI_EN_PRODUCT = re.compile(
    r"(?i)\b("
    r"drawer|organizer|organizers|makeup|vanity|bathroom|kitchen|office|desk|"
    r"storage|bins|trays|pads|non[- ]?slip|set|piece|pieces|clear|plastic"
    r")\b"
)


def load_rules(path: Path | None = None) -> dict[str, Any]:
    rules_path = path or DEFAULT_RULES
    with rules_path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _scan_banned(text: str, patterns: list[dict[str, str]]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if not text:
        return hits
    for item in patterns:
        pat = item["pattern"]
        if re.search(pat, text):
            hits.append({"pattern": pat, "reason": item.get("reason", "banned"), "snippet": text[:120]})
    return hits


def _is_all_caps_title(title: str) -> bool:
    letters = [c for c in title if c.isalpha()]
    if len(letters) < 8:
        return False
    upper = sum(1 for c in letters if c.isupper())
    return upper / len(letters) >= 0.85


def _has_punctuation(title: str) -> bool:
    # MELI: no punctuation/symbols (spaces and alphanumerics OK; allow ñ/á etc.)
    return bool(re.search(r"[^\w\s]", title, flags=re.UNICODE))


def check_title(title: str, market: str, rules: dict[str, Any] | None = None) -> dict[str, Any]:
    rules = rules or load_rules()
    markets = rules["markets"]
    if market not in markets:
        raise ValueError(f"unknown market: {market}")
    cfg = markets[market]
    reasons: list[str] = []
    n = len(title or "")

    max_c = cfg.get("title_max_chars")
    min_c = cfg.get("title_min_chars")
    if max_c is not None and n > max_c:
        reasons.append(f"title length {n} > max {max_c}")
    if min_c is not None and n < min_c:
        reasons.append(f"title length {n} < min {min_c}")

    style = (rules.get("title_style") or {}).get(market) or {}

    if style.get("no_all_caps") and _is_all_caps_title(title or ""):
        reasons.append(f"ALL-CAPS title rejected for {market}")
    for promo in style.get("no_promo_words") or []:
        if promo.lower() in (title or "").lower():
            reasons.append(f"promo word banned: {promo}")

    if style.get("no_punctuation") and _has_punctuation(title or ""):
        reasons.append(f"punctuation/symbols not allowed in {market} title")

    if style.get("no_english_product_nouns") and _MELI_EN_PRODUCT.search(title or ""):
        m = _MELI_EN_PRODUCT.search(title or "")
        reasons.append(f"English product word in {market} title: {m.group(0)!r}")

    banned_hits = _scan_banned(title or "", rules.get("banned_claim_patterns") or [])
    for h in banned_hits:
        reasons.append(f"banned claim in title: {h['reason']}")

    return {
        "market": market,
        "field": "title",
        "pass": len(reasons) == 0,
        "length": n,
        "reasons": reasons,
        "banned_hits": banned_hits,
    }


def check_text_fields(
    fields: dict[str, str | list[str]],
    market: str,
    rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Scan all string / list-of-string fields for banned claims + Amazon bullet limits."""
    rules = rules or load_rules()
    reasons: list[str] = []
    banned_hits: list[dict[str, str]] = []
    cfg = rules["markets"].get(market) or {}

    def walk(name: str, value: Any) -> None:
        if isinstance(value, list):
            for i, item in enumerate(value):
                walk(f"{name}[{i}]", item)
            return
        if not isinstance(value, str):
            return
        hits = _scan_banned(value, rules.get("banned_claim_patterns") or [])
        for h in hits:
            banned_hits.append({**h, "field": name})
            reasons.append(f"banned claim in {name}: {h['reason']}")

    for k, v in fields.items():
        walk(k, v)

    if market == "amazon_us":
        bullets = fields.get("bullets") or fields.get("highlights") or []
        if isinstance(bullets, list):
            bmin = cfg.get("bullet_min_chars", 10)
            bmax = cfg.get("bullet_max_chars", 255)
            if len(bullets) != 5:
                reasons.append(f"Amazon expects 5 bullets, got {len(bullets)}")
            for i, b in enumerate(bullets):
                if not isinstance(b, str):
                    reasons.append(f"bullet[{i}] not a string")
                    continue
                ln = len(b)
                if ln < bmin or ln > bmax:
                    reasons.append(f"bullet[{i}] length {ln} not in [{bmin},{bmax}]")
        backend = fields.get("backend_search_terms") or ""
        if isinstance(backend, str) and backend:
            nbytes = len(backend.encode("utf-8"))
            lim = cfg.get("backend_search_terms_max_bytes", 249)
            if nbytes > lim:
                reasons.append(f"backend_search_terms {nbytes} bytes > {lim}")
        ih = fields.get("item_highlights") or ""
        if isinstance(ih, str) and ih:
            lim = cfg.get("item_highlights_max_chars", 125)
            if len(ih) > lim:
                reasons.append(f"item_highlights length {len(ih)} > {lim}")

    # Shopee family description floor
    if market.startswith("shopee_"):
        desc = fields.get("description") or ""
        dmin = cfg.get("description_min_chars", 100)
        if isinstance(desc, str) and len(desc) < dmin:
            reasons.append(f"Shopee description length {len(desc)} < min {dmin}")

    return {
        "market": market,
        "pass": len(reasons) == 0,
        "reasons": reasons,
        "banned_hits": banned_hits,
    }


def gate_listing(listing: dict[str, Any], market: str, rules: dict[str, Any] | None = None) -> dict[str, Any]:
    """Full gate: title + body fields. Returns structured pass/fail."""
    rules = rules or load_rules()
    title = listing.get("title") or ""
    title_result = check_title(title, market, rules)

    body = {
        k: v
        for k, v in listing.items()
        if k
        not in (
            "title",
            "compliance",
            "market",
            "keywords",
            "keyword_library",
        )
    }
    # Still scan keywords as text
    kw = listing.get("keywords") or listing.get("keyword_library")
    if kw is not None:
        body["keywords"] = kw if isinstance(kw, (str, list)) else str(kw)

    body_result = check_text_fields(body, market, rules)
    reasons = list(title_result["reasons"]) + list(body_result["reasons"])
    passed = title_result["pass"] and body_result["pass"]
    return {
        "market": market,
        "pass": passed,
        "title": title_result,
        "body": body_result,
        "reasons": reasons,
    }
