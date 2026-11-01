"""Local Chinese demo shell — stdlib HTTP server over pipeline.build_pack.

Auth: HTTP Basic (any username; password = DEMO_SHELL_PASSWORD, default demo2026).
Bind: DEMO_SHELL_HOST / DEMO_SHELL_PORT (default 127.0.0.1:8765).
"""
from __future__ import annotations

import base64
import json
import os
import secrets
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]  # commercial/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.pack import build_pack  # noqa: E402
from pipeline.render_md import render_listing_pack_md  # noqa: E402

from demo_shell.sku_form import assemble_sku, fixture_for_form  # noqa: E402

TEMPLATES = Path(__file__).resolve().parent / "templates"
TMP_DIR = Path(__file__).resolve().parent / "tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_PASSWORD = "demo2026"
HOST = os.environ.get("DEMO_SHELL_HOST", "127.0.0.1")
PORT = int(os.environ.get("DEMO_SHELL_PORT", "8765"))

# In-memory last packs for download (token -> md text)
_PACK_STORE: dict[str, dict[str, Any]] = {}
_STORE_LOCK = threading.Lock()
_STORE_MAX = 32


def _password() -> str:
    return os.environ.get("DEMO_SHELL_PASSWORD", DEFAULT_PASSWORD)


def _check_basic_auth(header: str | None) -> bool:
    if not header or not header.startswith("Basic "):
        return False
    try:
        raw = base64.b64decode(header[6:].strip()).decode("utf-8")
    except Exception:
        return False
    if ":" not in raw:
        return False
    _user, pwd = raw.split(":", 1)
    return secrets.compare_digest(pwd, _password())


def _ui_summary(pack: dict[str, Any]) -> dict[str, Any]:
    markets_out: dict[str, Any] = {}
    for key, label in (
        ("amazon_us", "Amazon EN (US)"),
        ("shopee_id", "Shopee ID"),
        ("meli_mx", "MELI MX"),
    ):
        m = (pack.get("markets") or {}).get(key) or {}
        comp = m.get("compliance") or {}
        lib = m.get("keyword_library") or {}
        passed = bool(comp.get("pass"))
        markets_out[key] = {
            "label": label,
            "title": m.get("title") or "",
            "bullets": list(m.get("bullets") or []),
            "description": m.get("description") or "",
            "description_preview": (m.get("description") or "")[:400],
            "keywords_primary": list(lib.get("primary") or m.get("keywords") or []),
            "compliance_pass": passed,
            "compliance_reasons": list(comp.get("reasons") or []),
            "title_length": (comp.get("title") or {}).get("length"),
            "light": "green" if passed else "red",
        }

    listable = bool(pack.get("listable"))
    hr = pack.get("human_review_required") or []
    overall_light = "green" if listable else "red"
    if listable and hr:
        overall_light = "yellow"

    return {
        "listable": listable,
        "overall_light": overall_light,
        "human_review_required": hr,
        "human_review_count": len(hr),
        "generated_at": pack.get("generated_at"),
        "keyword_library": pack.get("keyword_library") or {},
        "compliance": pack.get("compliance") or {},
        "markets": markets_out,
        "sku": pack.get("sku") or {},
    }


def _store_pack(pack: dict[str, Any], md: str) -> str:
    token = secrets.token_urlsafe(16)
    with _STORE_LOCK:
        _PACK_STORE[token] = {"md": md, "pack": pack}
        while len(_PACK_STORE) > _STORE_MAX:
            _PACK_STORE.pop(next(iter(_PACK_STORE)))
    return token


class DemoHandler(BaseHTTPRequestHandler):
    server_version = "AdvertoolsDemoShell/0.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _require_auth(self) -> bool:
        if _check_basic_auth(self.headers.get("Authorization")):
            return True
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="advertools demo shell"')
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Unauthorized - set DEMO_SHELL_PASSWORD (default demo2026)".encode("utf-8"))
        return False

    def _send(
        self,
        code: int,
        body: bytes,
        content_type: str,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, code: int, obj: Any) -> None:
        raw = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        self._send(code, raw, "application/json; charset=utf-8")

    def do_GET(self) -> None:
        if not self._require_auth():
            return
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            html = (TEMPLATES / "index.html").read_bytes()
            self._send(200, html, "text/html; charset=utf-8")
            return

        if path == "/api/health":
            self._send_json(200, {"ok": True, "service": "demo_shell"})
            return

        if path == "/api/fixture":
            self._send_json(200, fixture_for_form())
            return

        if path.startswith("/api/download/"):
            token = path[len("/api/download/") :].strip("/")
            with _STORE_LOCK:
                entry = _PACK_STORE.get(token)
            if not entry:
                self._send_json(404, {"error": "download token expired or unknown"})
                return
            md = entry["md"].encode("utf-8")
            fname = "listing_pack.md"
            self._send(
                200,
                md,
                "text/markdown; charset=utf-8",
                {
                    "Content-Disposition": f'attachment; filename="{fname}"',
                },
            )
            return

        self._send_json(404, {"error": "not found", "path": path})

    def do_POST(self) -> None:
        if not self._require_auth():
            return
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"

        if path == "/api/generate":
            try:
                payload = json.loads(raw.decode("utf-8") or "{}")
            except json.JSONDecodeError as e:
                self._send_json(400, {"error": f"invalid JSON: {e}"})
                return
            try:
                sku = assemble_sku(payload)
            except Exception as e:
                self._send_json(400, {"error": f"SKU assemble failed: {e}"})
                return
            try:
                pack = build_pack(sku, source_fixture="demo_shell")
                md = render_listing_pack_md(pack)
                token = _store_pack(pack, md)
                # also write a temp file for operators
                out = TMP_DIR / f"{token}_listing_pack.md"
                out.write_text(md, encoding="utf-8")
                summary = _ui_summary(pack)
                summary["download_token"] = token
                summary["download_url"] = f"/api/download/{token}"
                summary["md"] = md
                self._send_json(200, summary)
            except Exception as e:
                self._send_json(500, {"error": f"generate failed: {e}"})
            return

        self._send_json(404, {"error": "not found", "path": path})


def main(argv: list[str] | None = None) -> int:
    host = HOST
    port = PORT
    if argv:
        # optional: python -m demo_shell --port 8765
        args = list(argv)
        if "--host" in args:
            i = args.index("--host")
            host = args[i + 1]
        if "--port" in args:
            i = args.index("--port")
            port = int(args[i + 1])

    httpd = ThreadingHTTPServer((host, port), DemoHandler)
    print(
        f"demo_shell listening on http://{host}:{port}/\n"
        f"  Basic Auth password: env DEMO_SHELL_PASSWORD "
        f"(default '{DEFAULT_PASSWORD}')\n"
        f"  commercial ROOT: {ROOT}",
        flush=True,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down", flush=True)
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
