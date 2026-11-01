# adapters/ — Step 1 marketplace listing packs

Generate Amazon US (EN), Shopee SEA (ID / TH / PH), and Mercado Libre LatAm
(MX / BR / AR) listing copy from a SKU JSON fixture, then score with the
compliance gate.

## Layout

| File | Role |
| --- | --- |
| `compliance_gate.py` | Load `rules/compliance.yaml`; title length + banned claims + market style |
| `keyword_engine.py` | Core-market keywords via advertools (`word_frequency`, `kw_generate`, `ad_from_string`) |
| `amazon_en.py` | Amazon US EN — title ≤75, 5 bullets, item highlights, backend terms |
| `shopee_id.py` | Shopee ID — Bahasa title 25–100, keywords (`organizer laci`, `sekat laci`) |
| `shopee_th.py` | Shopee TH — Thai title 25–100, keywords (`กล่องแบ่งลิ้นชัก`, `ที่จัดระเบียบลิ้นชัก`) |
| `shopee_ph.py` | Shopee PH — English PH title 25–100, keywords (`drawer organizer`, `drawer divider`) |
| `meli_mx.py` | MELI MX — Spanish title ≤60, no punctuation, no Spanglish |
| `meli_br.py` | MELI BR — Portuguese title ≤60, no punctuation, no EN product nouns |
| `meli_ar.py` | MELI AR — Spanish AR title ≤60, no punctuation, no Spanglish |
| `generate_all.py` | Orchestrator for all markets |

## Run (commercial venv)

```bash
cd /workspace/advertools/commercial
source .venv/bin/activate

# Generate packs + write fixtures/drawer_organizer_25pcs.generated.json
python scripts/generate_listings.py

# Smoke assertions (exit 0 on PASS)
python scripts/smoke_adapters.py
```

Optional flags:

```bash
python scripts/generate_listings.py \
  --fixture fixtures/drawer_organizer_25pcs.json \
  --out fixtures/drawer_organizer_25pcs.generated.json
```

## Python API

```python
from adapters.generate_all import generate_from_path, generate_all
from adapters import amazon_en, shopee_id, shopee_th, shopee_ph, meli_mx, meli_br, meli_ar

result = generate_from_path()  # uses golden drawer fixture
am = amazon_en.generate(sku_dict)
```

## Keywords (Amazon US, Shopee ID, MELI MX)

Those three markets do **not** keep a hand-written keyword list. `keyword_engine.build_keywords`
expands seeds with upstream advertools, and the adapter then runs `gate_listing`
(banned claims + title/bullet length). Title and bullet copy stay in the adapters.

Seed phrases are product stems plus an intent lexicon. `word_frequency` drops any
intent the SKU corpus does not contain (scenes, pad / clear / multi-size features,
piece count). `kw_generate` (Phrase, `max_len=3`) permutes stems × surviving words.
`ad_from_string` slices a count + stem blurb into long-tail slots.

| Market | Product stems (`kw_generate` products) | Required stems |
| --- | --- | --- |
| `amazon_us` | `drawer organizer`, `clear drawer organizer`, `plastic drawer organizer` | — |
| `shopee_id` | `organizer laci`, `sekat laci`, `kotak penyimpanan laci` | `organizer laci`, `sekat laci` |
| `meli_mx` | `organizador de cajones`, `separadores de cajones`, `bandejas transparentes` | — |

Intent examples the drawer fixture keeps when the scene is present: EN `makeup`,
`vanity`, `bathroom`, `kitchen`, `desk`; ID `makeup`, `dapur`, `kamar mandi`;
ES `maquillaje`, `cocina`, `bano`. Feature seeds such as `non slip` / `anti slip` /
`antideslizante` are included only when the SKU has pads.

Shopee TH, Shopee PH, MELI BR, and MELI AR still use adapter-local keyword lists.

## Hard rules (reminders)

- Care: wipe / hand-rinse only — never claim dishwasher-safe
- No absolute BPA / fake social proof / child-safety seals
- Amazon title hard ≤75 (overflow ideas → item highlights ≤125)
- MELI (MX/BR/AR): local nouns first; spaces only; no EN product nouns in title
- Shopee: no ALL-CAPS, no promo spam; ID/TH/PH keyword stems required per market
