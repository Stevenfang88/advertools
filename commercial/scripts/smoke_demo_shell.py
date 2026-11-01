"""Step 3 smoke: assemble fixture SKU → build_pack via demo_shell helpers (no server)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from demo_shell.sku_form import assemble_sku, load_default_fixture
from pipeline.pack import build_pack
from pipeline.render_md import render_listing_pack_md


def main() -> int:
    sku = assemble_sku(load_default_fixture())
    pack = build_pack(sku, source_fixture="smoke_demo_shell")
    md = render_listing_pack_md(pack)
    titles = {k: (v.get("title") or "") for k, v in pack["markets"].items()}
    ok = bool(pack["listable"]) and all(titles.values()) and len(md) > 100
    print(f"listable={pack['listable']}")
    print(f"human_review={len(pack.get('human_review_required') or [])}")
    for k, t in titles.items():
        print(f"  {k}: {t}")
    print(f"md_chars={len(md)}")
    print("SMOKE_OK" if ok else "SMOKE_FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
