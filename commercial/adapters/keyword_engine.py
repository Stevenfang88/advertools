"""Batch-generate core-market keyword libraries with upstream advertools.

Amazon US (EN), Shopee Indonesia, and Mercado Libre Mexico no longer keep a
hand-written ``keywords`` / ``keyword_library``. :func:`build_keywords` expands
a small per-market seed (product stems + an intent lexicon) through upstream
advertools, then each adapter scores the full listing with
:func:`adapters.compliance_gate.gate_listing`.

Nothing under ``advertools/`` is modified. Title, bullet, and description copy
stay in the market adapters.

Generation path
---------------
1. Build a short SKU corpus: localized scene lines, feature lines that the SKU
   actually supports (pads, clear material, multiple sizes), and a spec line
   with piece count and size count.
2. :func:`advertools.word_frequency` scores that corpus (unigrams and bigrams,
   market stopwords). Intent seeds with a zero score are dropped, so a scene
   that is not on the SKU does not become a keyword.
3. :func:`advertools.kw_generate` permutes product stems with the surviving
   words (Phrase match only, ``max_len=3``, order matters). Phrase text is the
   listing keyword. Modified-broad (``+``) and exact-bracket rows are not
   requested — those are Google Ads match types, not marketplace terms.
4. :func:`advertools.ad_from_string` slices one SKU search blurb into fixed
   character slots. Non-empty slots that still contain a product stem are
   extra long-tail lines.
5. Phrases that match ``rules/compliance.yaml`` banned-claim patterns are
   removed. Shopee ID then pins ``organizer laci`` and ``sekat laci``.

The emitted library is a short primary + long-tail cut of the generated pool
(head stem × ranked intents, plus spec / slot lines), not the raw permutation
table. ``keyword_generation`` on the listing records the advertools calls.
"""
from __future__ import annotations

import re
from typing import Any

import advertools as adv

from .compliance_gate import load_rules

CORE_MARKETS = ("amazon_us", "shopee_id", "meli_mx")

# Pinned on every Shopee ID library, even if a later cut would drop them.
SHOPEE_ID_REQUIRED_KEYWORDS = ("organizer laci", "sekat laci")

# English fixture scenes → marketplace wording. Unmapped EN scenes are kept
# as their own phrase; ID/ES skip unmapped scenes so English nouns do not leak.
_SCENE_MAP: dict[str, dict[str, str]] = {
    "amazon_us": {
        "makeup vanity": "makeup vanity",
        "bathroom drawer": "bathroom",
        "kitchen utensil drawer": "kitchen utensil",
        "office desk drawer": "office desk",
        "jewelry accessories": "jewelry",
    },
    "shopee_id": {
        "makeup vanity": "makeup",
        "bathroom drawer": "kamar mandi",
        "kitchen utensil drawer": "dapur",
        "office desk drawer": "meja kerja",
        "jewelry accessories": "perhiasan",
    },
    "meli_mx": {
        "makeup vanity": "maquillaje",
        "bathroom drawer": "bano",
        "kitchen utensil drawer": "cocina fregadero",
        "office desk drawer": "oficina escritorio",
        "jewelry accessories": "joyas",
    },
}

# Intent lexicon order is merchandising priority among ties. word_frequency
# still drops any phrase that does not occur in this SKU's corpus.
_SCENE_LEXICON: dict[str, tuple[str, ...]] = {
    "amazon_us": (
        "makeup",
        "vanity",
        "bathroom",
        "kitchen",
        "desk",
        "office",
        "jewelry",
        "utensil",
    ),
    "shopee_id": (
        "makeup",
        "dapur",
        "kamar mandi",
        "meja kerja",
        "perhiasan",
    ),
    "meli_mx": (
        "maquillaje",
        "cocina",
        "bano",
        "oficina",
        "escritorio",
        "joyas",
        "fregadero",
    ),
}

_PRODUCTS: dict[str, tuple[str, ...]] = {
    "amazon_us": (
        "drawer organizer",
        "clear drawer organizer",
        "plastic drawer organizer",
    ),
    "shopee_id": (
        "organizer laci",
        "sekat laci",
        "kotak penyimpanan laci",
    ),
    "meli_mx": (
        "organizador de cajones",
        "separadores de cajones",
        "bandejas transparentes",
    ),
}

_STOPWORD_LANG = {
    "amazon_us": "english",
    "shopee_id": "indonesian",
    "meli_mx": "spanish",
}

# kw_generate campaign name, ad_from_string slot widths, library cuts.
_MARKET_CFG: dict[str, dict[str, Any]] = {
    "amazon_us": {
        "required": (),
        "scene_limit": 5,
        "primary_n": 8,
        "long_tail_n": 7,
        "ad_keep": 2,
        "strip_punct": False,
    },
    "shopee_id": {
        "required": SHOPEE_ID_REQUIRED_KEYWORDS,
        "scene_limit": 4,
        "primary_n": 6,
        "long_tail_n": 7,
        "ad_keep": 2,
        "strip_punct": False,
    },
    "meli_mx": {
        "required": (),
        "scene_limit": 4,
        "primary_n": 6,
        "long_tail_n": 7,
        "ad_keep": 2,
        "strip_punct": True,
    },
}


def required_keywords(market: str) -> tuple[str, ...]:
    """Stems that must appear in ``keywords`` for ``market`` (may be empty)."""
    if market not in _MARKET_CFG:
        raise ValueError(f"keyword engine supports {CORE_MARKETS}, not {market!r}")
    return tuple(_MARKET_CFG[market]["required"])


def _normalize(text: str, *, strip_punct: bool) -> str:
    text = text.replace("+", " ").replace("[", " ").replace("]", " ")
    text = text.replace('"', " ")
    if strip_punct:
        text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip().lower()


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.casefold()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _is_clear(sku: dict[str, Any]) -> bool:
    blob = f"{sku.get('color') or ''} {sku.get('material') or ''}".lower()
    return any(tok in blob for tok in ("clear", "transparent", "transparente", "bening"))


def _has_pads(sku: dict[str, Any]) -> bool:
    return bool(sku.get("pad_count")) or bool(sku.get("pad_material"))


def _feature_seeds(sku: dict[str, Any], market: str) -> list[str]:
    """Feature atoms the SKU can support. Frequency still has to see them."""
    pads = _has_pads(sku)
    multi = len(sku.get("sizes") or []) > 1
    clear = _is_clear(sku)
    if market == "amazon_us":
        seeds = []
        if pads:
            seeds.append("non slip")
        if multi:
            seeds.append("nestable")
        return seeds
    if market == "shopee_id":
        seeds = []
        if pads:
            seeds.append("anti slip")
        if clear:
            seeds.append("bening")
        return seeds
    if market == "meli_mx":
        seeds = []
        if pads:
            seeds.append("antideslizante")
        if clear:
            seeds.append("transparente")
        return seeds
    return []


def _spec_seeds(sku: dict[str, Any], market: str) -> list[str]:
    pcs = sku.get("piece_count")
    n_sizes = len(sku.get("sizes") or [])
    if market == "amazon_us":
        seeds = []
        if pcs:
            seeds.append(f"{pcs} piece")
        if n_sizes:
            seeds.append(f"{n_sizes} sizes")
        return seeds
    if market == "shopee_id":
        seeds = []
        if pcs:
            seeds.append(f"{pcs} pcs")
        if n_sizes:
            seeds.append(f"{n_sizes} ukuran")
        return seeds
    if market == "meli_mx":
        seeds = []
        if pcs:
            seeds.append(f"{pcs} pzs")
        if n_sizes:
            seeds.append(f"{n_sizes} tamanos")
        return seeds
    return []


def _scene_documents(sku: dict[str, Any], market: str) -> tuple[list[str], list[str]]:
    """Return (corpus lines, extra EN phrases for scenes outside the map)."""
    mapping = _SCENE_MAP[market]
    docs: list[str] = []
    extra: list[str] = []
    for raw in sku.get("scenes") or []:
        key = str(raw)
        if key in mapping:
            docs.append(mapping[key])
            continue
        if market == "amazon_us":
            cleaned = _normalize(key, strip_punct=False)
            if cleaned:
                docs.append(cleaned)
                extra.append(cleaned)
    return docs, extra


def _freq_maps(
    docs: list[str],
    weights: list[int],
    stopwords: set[str],
) -> tuple[dict[str, float], dict[str, float], list[str]]:
    """Unigram and bigram weighted frequencies, plus top unigrams for metadata."""
    if not docs:
        return {}, {}, []
    uni = adv.word_frequency(
        docs,
        num_list=weights,
        phrase_len=1,
        rm_words=stopwords,
    )
    bi = adv.word_frequency(
        docs,
        num_list=weights,
        phrase_len=2,
        rm_words=stopwords,
    )

    def _as_map(frame: Any) -> dict[str, float]:
        if frame is None or frame.empty:
            return {}
        return {str(w): float(s) for w, s in zip(frame["word"], frame["wtd_freq"])}

    uni_map = _as_map(uni)
    bi_map = _as_map(bi)
    if uni is None or uni.empty:
        top: list[str] = []
    else:
        ordered = uni.sort_values(["wtd_freq", "word"], ascending=[False, True])
        top = [str(w) for w in ordered["word"].head(12).tolist()]
    return uni_map, bi_map, top


def _phrase_score(phrase: str, uni: dict[str, float], bi: dict[str, float]) -> float:
    parts = phrase.lower().split()
    if not parts:
        return 0.0
    if len(parts) >= 2:
        windows = [bi.get(f"{a} {b}", 0.0) for a, b in zip(parts, parts[1:])]
        if all(windows):
            return float(sum(windows))
    if all(uni.get(part, 0.0) > 0 for part in parts):
        return float(sum(uni.get(part, 0.0) for part in parts))
    return 0.0


def _select_scored(candidates: list[str], uni: dict[str, float], bi: dict[str, float], limit: int) -> list[str]:
    ranked = [c for c in candidates if _phrase_score(c, uni, bi) > 0]
    return _dedupe(ranked)[:limit]


def _banned_patterns(rules: dict[str, Any]) -> list[re.Pattern[str]]:
    compiled: list[re.Pattern[str]] = []
    for item in rules.get("banned_claim_patterns") or []:
        compiled.append(re.compile(item["pattern"]))
    return compiled


def _allow(phrase: str, banned: list[re.Pattern[str]]) -> bool:
    if not phrase or len(phrase) > 80:
        return False
    return not any(pat.search(phrase) for pat in banned)


def _search_chunks(
    market: str,
    sku: dict[str, Any],
    products: list[str],
    feature_words: list[str],
) -> list[str]:
    """Two search lines whose lengths become ``ad_from_string`` slot widths.

    Slot width tracks the chunk, so a longer piece-count does not slice a
    product stem in half. Scene words are appended after the chunks and land
    in the remainder, not in these slots.
    """
    pcs = sku.get("piece_count") or 0
    n_sizes = len(sku.get("sizes") or [])
    head = products[0]
    second = products[1] if len(products) > 1 else head
    feats = [w for w in feature_words if w]
    if market == "amazon_us":
        first = f"{pcs} piece clear plastic {head}"
        second_line = " ".join(
            part for part in (f"{n_sizes} sizes" if n_sizes else "", " ".join(feats), head) if part
        )
        return [first, second_line]
    if market == "shopee_id":
        material = "plastik bening" if "bening" in feats else "plastik"
        first = f"{head} {pcs} pcs {material}"
        slip = "anti slip" if "anti slip" in feats else ""
        second_line = " ".join(
            part for part in (second, f"{n_sizes} ukuran" if n_sizes else "", slip) if part
        )
        return [first, second_line]
    material = "plastico transparente" if "transparente" in feats else "plastico"
    first = f"{head} {pcs} pzs"
    second_line = f"{material} {second}"
    return [first, second_line]


def _blurb_and_slots(
    market: str,
    sku: dict[str, Any],
    products: list[str],
    feature_words: list[str],
    scene_words: list[str],
) -> tuple[str, tuple[int, ...]]:
    chunks = [re.sub(r"\s+", " ", c).strip() for c in _search_chunks(market, sku, products, feature_words)]
    chunks = [c for c in chunks if c]
    scenes = " ".join(scene_words)
    tail = " ".join(part for part in (scenes, products[0]) if part)
    blurb = " ".join(part for part in (*chunks, tail) if part)
    slots = tuple(len(chunk) for chunk in chunks)
    return blurb, slots


def _stem_boundary_ok(phrase: str, products: list[str]) -> bool:
    """True when ``phrase`` contains a full stem and does not cut one in half."""
    tokens = phrase.split()
    stems = [p.split() for p in products]
    for stem in stems:
        for n in range(1, len(stem)):
            if tokens[-n:] == stem[:n] or tokens[:n] == stem[-n:]:
                return False
    return any(" ".join(stem) in phrase for stem in stems)


def _ad_slots(
    blurb: str,
    slots: tuple[int, ...],
    products: list[str],
    *,
    strip_punct: bool,
    banned: list[re.Pattern[str]],
    keep: int,
) -> list[str]:
    """Keep ad_from_string slices that still name a whole product stem."""
    if not blurb or not slots:
        return []
    raw_slots = adv.ad_from_string(blurb, slots)
    kept: list[str] = []
    for raw in raw_slots:
        phrase = _normalize(raw or "", strip_punct=strip_punct)
        if not _allow(phrase, banned):
            continue
        if not _stem_boundary_ok(phrase, [p.casefold() for p in products]):
            continue
        if phrase not in kept:
            kept.append(phrase)
        if len(kept) >= keep:
            break
    return kept


def _product_first_pool(
    frame: Any,
    products: list[str],
    words: list[str],
) -> dict[tuple[str, tuple[str, ...]], str]:
    """Map (product, sorted intents) → product-first Phrase keyword.

    Among permutations, prefer intent order that follows the seed list
    (makeup then vanity, not vanity then makeup).
    """
    order = {w.casefold(): i for i, w in enumerate(words)}
    best: dict[tuple[str, tuple[str, ...]], tuple[tuple[int, ...], str]] = {}
    if frame is None or frame.empty:
        return {}
    for rec in frame.to_dict("records"):
        prod = str(rec.get("Ad Group") or "").strip().lower()
        kw = _normalize(str(rec.get("Keyword") or ""), strip_punct=False)
        if not prod or not kw.startswith(prod + " "):
            continue
        labels = str(rec.get("Labels") or "")
        intents = tuple(part.strip().casefold() for part in labels.split(";") if part.strip())
        if not intents:
            continue
        rank = tuple(order.get(part, 99) for part in intents)
        key = (prod, tuple(sorted(intents)))
        cand = (rank, kw)
        prev = best.get(key)
        if prev is None or cand < prev:
            best[key] = cand
    return {key: kw for key, (_rank, kw) in best.items()}


def _lookup(
    pool: dict[tuple[str, tuple[str, ...]], str],
    product: str,
    intents: tuple[str, ...],
) -> str | None:
    key = (product.casefold(), tuple(sorted(i.casefold() for i in intents)))
    return pool.get(key)


def build_keywords(sku: dict[str, Any], market: str) -> dict[str, Any]:
    """Return ``keywords``, ``keyword_library``, and ``keyword_generation``.

    Callers pass the listing through :func:`adapters.compliance_gate.gate_listing`
    after merging these fields with title and bullet copy.
    """
    if market not in _MARKET_CFG:
        raise ValueError(f"keyword engine supports {CORE_MARKETS}, not {market!r}")

    cfg = _MARKET_CFG[market]
    rules = load_rules()
    banned = _banned_patterns(rules)
    strip_punct = bool(cfg["strip_punct"])
    products = list(_PRODUCTS[market])
    required = [str(s) for s in cfg["required"]]
    stopwords = set(adv.stopwords[_STOPWORD_LANG[market]])

    scene_docs, extra_scenes = _scene_documents(sku, market)
    feature_candidates = _feature_seeds(sku, market)
    spec_candidates = _spec_seeds(sku, market)

    docs: list[str] = []
    weights: list[int] = []
    for line in scene_docs:
        docs.append(line)
        weights.append(5)
    for line in feature_candidates:
        docs.append(line)
        weights.append(3)
    if spec_candidates or products:
        docs.append(" ".join([*spec_candidates, products[0]]))
        weights.append(1)

    uni, bi, top_words = _freq_maps(docs, weights, stopwords)
    scene_words = _select_scored(
        [*_SCENE_LEXICON[market], *extra_scenes],
        uni,
        bi,
        int(cfg["scene_limit"]),
    )
    feature_words = _select_scored(feature_candidates, uni, bi, len(feature_candidates))
    spec_words = _select_scored(spec_candidates, uni, bi, len(spec_candidates))
    words = _dedupe([*scene_words, *feature_words, *spec_words])

    frame = None
    if words:
        frame = adv.kw_generate(
            products,
            words,
            max_len=3,
            match_types=("Phrase",),
            capitalize_adgroups=False,
            order_matters=True,
            campaign_name=f"listing_{market}",
        )
    pool = _product_first_pool(frame, products, words)
    head = products[0]
    scene_set = {w.casefold() for w in scene_words}

    def _clean(phrase: str | None) -> str | None:
        if not phrase:
            return None
        norm = _normalize(phrase, strip_punct=strip_punct)
        if not _allow(norm, banned):
            return None
        return norm

    scene_phrases = [
        p
        for w in scene_words
        if (p := _clean(_lookup(pool, head, (w,))))
    ]
    feature_phrases = [
        p
        for w in feature_words
        if (p := _clean(_lookup(pool, head, (w,))))
    ]
    spec_phrases = [
        p
        for w in spec_words
        if (p := _clean(_lookup(pool, head, (w,))))
    ]

    three: list[tuple[tuple[int, ...], str]] = []
    scene_index = {w.casefold(): i for i, w in enumerate(scene_words)}
    for (prod, intents), kw in pool.items():
        if prod != head.casefold() or len(intents) != 2:
            continue
        if not set(intents).issubset(scene_set):
            continue
        cleaned = _clean(kw)
        if not cleaned:
            continue
        rank = tuple(sorted(scene_index.get(i, 99) for i in intents))
        three.append((rank, cleaned))
    three.sort(key=lambda item: (item[0], item[1]))
    three_phrases = _dedupe([kw for _rank, kw in three])

    blurb, ad_widths = _blurb_and_slots(market, sku, products, feature_words, scene_words)
    ad_phrases = _ad_slots(
        blurb,
        ad_widths,
        products,
        strip_punct=strip_punct,
        banned=banned,
        keep=int(cfg["ad_keep"]),
    )

    stems = _dedupe([*required, *[_clean(p) or "" for p in products]])
    stems = [s for s in stems if s and _allow(s, banned)]
    primary_n = max(int(cfg["primary_n"]), len(required))
    primary = _dedupe([*stems, *scene_phrases, *feature_phrases])[:primary_n]
    # Required stems stay even if a cut would drop them.
    for stem in reversed(required):
        cleaned = _clean(stem)
        if cleaned and cleaned not in primary:
            primary.insert(0, cleaned)
    primary = _dedupe(primary)

    used = {p.casefold() for p in primary}
    long_tail: list[str] = []
    # Spec and feature lines show kw_generate; the first 3-word phrase shows
    # max_len=3; ad slots show ad_from_string. Further permutations fill only
    # if those sources do not already cover the long-tail cut.
    for source in (
        spec_phrases,
        feature_phrases,
        three_phrases[:1],
        ad_phrases,
        three_phrases[1:],
        scene_phrases,
    ):
        for phrase in source:
            if phrase.casefold() in used:
                continue
            long_tail.append(phrase)
            used.add(phrase.casefold())
            if len(long_tail) >= int(cfg["long_tail_n"]):
                break
        if len(long_tail) >= int(cfg["long_tail_n"]):
            break

    keywords = _dedupe([*primary, *long_tail])
    rows = 0 if frame is None else int(len(frame))
    generation = {
        "engine": "advertools",
        "module": "adapters.keyword_engine",
        "apis": ["word_frequency", "kw_generate", "ad_from_string"],
        "market": market,
        "campaign_name": f"listing_{market}",
        "match_types": ["Phrase"],
        "max_len": 3,
        "order_matters": True,
        "products": products,
        "words": words,
        "scene_words": scene_words,
        "feature_words": feature_words,
        "spec_words": spec_words,
        "required_stems": required,
        "word_frequency_top": top_words,
        "kw_generate_rows": rows,
        "ad_from_string_slots": ad_phrases,
        "ad_from_string_widths": list(ad_widths),
    }
    return {
        "keywords": keywords,
        "keyword_library": {"primary": primary, "long_tail": long_tail},
        "keyword_generation": generation,
    }
