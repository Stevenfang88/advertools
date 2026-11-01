#!/usr/bin/env python3
"""CLI: generate Amazon / Shopee / MELI listing packs from a SKU fixture."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))  # allow `import commercial...` if needed
sys.path.insert(0, str(ROOT))

from adapters.generate_all import DEFAULT_FIXTURE, DEFAULT_OUT, generate_from_path  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate multi-market listing packs")
    ap.add_argument(
        "--fixture",
        type=Path,
        default=DEFAULT_FIXTURE,
        help="SKU JSON path (default: drawer_organizer_25pcs.json)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Output JSON path",
    )
    ap.add_argument(
        "--no-write",
        action="store_true",
        help="Print only; do not write output file",
    )
    args = ap.parse_args()

    result = generate_from_path(args.fixture, args.out, write=not args.no_write)
    markets = result["markets"]
    print("=== Listing packs ===")
    for key, pack in markets.items():
        comp = pack.get("compliance") or {}
        status = "PASS" if comp.get("pass") else "FAIL"
        print(f"\n[{key}] compliance={status} title_len={len(pack.get('title') or '')}")
        print(f"  title: {pack.get('title')}")
        kws = pack.get("keywords") or []
        print(f"  keywords (first 5): {kws[:5]}")
        if not comp.get("pass"):
            for r in comp.get("reasons") or []:
                print(f"  reason: {r}")
    print(f"\nall_compliance_pass={result.get('all_compliance_pass')}")
    if not args.no_write:
        print(f"wrote: {result.get('output_path')}")
    # Also dump compact JSON summary to stdout tail
    summary = {
        "all_compliance_pass": result.get("all_compliance_pass"),
        "titles": {k: v.get("title") for k, v in markets.items()},
        "output_path": result.get("output_path"),
    }
    print("\n" + json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if result.get("all_compliance_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
