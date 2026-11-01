"""CLI: one-command Listing Pack export (Step 2).

Usage (from commercial/ with venv active)::

    python -m pipeline.run --sku fixtures/drawer_organizer_25pcs.json --out-dir pipeline/out
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.pack import DEFAULT_OUT_DIR, DEFAULT_SKU, DEFAULT_T1, export_pack  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Export T1-aligned Listing Pack (Markdown + JSON + compliance)"
    )
    ap.add_argument(
        "--sku",
        type=Path,
        default=DEFAULT_SKU,
        help="SKU JSON path (default: fixtures/drawer_organizer_25pcs.json)",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Output directory (default: pipeline/out)",
    )
    ap.add_argument(
        "--t1",
        type=Path,
        default=DEFAULT_T1,
        help="Hand-written T1 Pack Markdown for polish compare",
    )
    args = ap.parse_args(argv)

    if not args.sku.is_file():
        print(f"ERROR: SKU not found: {args.sku}", file=sys.stderr)
        return 2

    meta = export_pack(args.sku, args.out_dir, t1_path=args.t1)
    listable = meta["listable"]
    print("=== Listing Pack export ===")
    print(f"listable={listable}")
    print(f"out_dir={meta['out_dir']}")
    print(f"md={meta['md_path']}")
    print(f"json={meta['json_path']}")
    print(f"compliance={meta['compliance_path']}")
    print(f"human_review_notes={meta['human_review_count']}")
    print("titles:")
    for k, t in meta["titles"].items():
        print(f"  {k}: {t}")
    summary = {
        "listable": listable,
        "md_path": meta["md_path"],
        "json_path": meta["json_path"],
        "compliance_path": meta["compliance_path"],
        "titles": meta["titles"],
    }
    print("\n" + json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if listable else 1


if __name__ == "__main__":
    raise SystemExit(main())
