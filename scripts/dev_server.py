#!/usr/bin/env python3
"""Local static server with API to persist dimension edits into data files."""

from __future__ import annotations

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = ROOT / "data" / "questions.json"
JS_PATH = ROOT / "data" / "questions.js"
TRASH_PATH = ROOT / "data" / "_deleted_dims.jsonl"
PORT = 8765


def load_data() -> dict:
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


def write_data(data: dict) -> None:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    JS_PATH.write_text(f"window.QUESTION_DATA = {payload};\n", encoding="utf-8")


def archive_deleted_dim(item_id: str, dim_idx: int, dim: dict) -> None:
    """Keep a recoverable copy when a dimension panel is deleted."""
    from datetime import datetime, timezone

    rec = {
        "deletedAt": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "itemId": item_id,
        "dimIdx": dim_idx,
        "dimension": dim,
    }
    TRASH_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TRASH_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    extensions_map = {
        **getattr(SimpleHTTPRequestHandler, "extensions_map", {}),
        ".js": "text/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".html": "text/html; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
    }

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/save-dim":
            self._save_dim()
            return
        if path == "/api/delete-dim":
            self._delete_dim()
            return
        if path == "/api/reorder-categories":
            self._reorder_categories()
            return
        self.send_error(404, "Not Found")

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _save_dim(self):
        try:
            body = self._read_json_body()
            item_id = str(body.get("itemId") or "")
            dim_idx = int(body.get("dimIdx"))
            detail = body.get("detail")
            if not item_id or not isinstance(detail, str):
                raise ValueError("invalid payload")
        except Exception:
            self._json(400, {"ok": False, "error": "invalid json"})
            return

        try:
            data = load_data()
            item = next((x for x in data.get("items", []) if x.get("id") == item_id), None)
            if not item:
                self._json(404, {"ok": False, "error": "item not found"})
                return
            dims = item.get("dimensions") or []
            if dim_idx < 0 or dim_idx >= len(dims):
                self._json(404, {"ok": False, "error": "dimension not found"})
                return
            dims[dim_idx]["detail"] = detail
            dims[dim_idx]["preserveBreaks"] = True
            label = body.get("label")
            if isinstance(label, str):
                cleaned = " ".join(label.split()).strip()
                if cleaned:
                    dims[dim_idx]["label"] = cleaned
                    dims[dim_idx]["summary"] = cleaned
            write_data(data)
            self._json(200, {"ok": True})
        except Exception as exc:
            self._json(500, {"ok": False, "error": str(exc)})

    def _delete_dim(self):
        try:
            body = self._read_json_body()
            item_id = str(body.get("itemId") or "")
            dim_idx = int(body.get("dimIdx"))
            if not item_id:
                raise ValueError("invalid payload")
        except Exception:
            self._json(400, {"ok": False, "error": "invalid json"})
            return

        try:
            data = load_data()
            item = next((x for x in data.get("items", []) if x.get("id") == item_id), None)
            if not item:
                self._json(404, {"ok": False, "error": "item not found"})
                return
            dims = item.get("dimensions") or []
            if dim_idx < 0 or dim_idx >= len(dims):
                self._json(404, {"ok": False, "error": "dimension not found"})
                return
            removed = dims.pop(dim_idx)
            try:
                archive_deleted_dim(item_id, dim_idx, removed)
            except Exception:
                # Archiving must not block delete persistence
                pass
            item["dimensions"] = dims
            write_data(data)
            self._json(200, {"ok": True})
        except Exception as exc:
            self._json(500, {"ok": False, "error": str(exc)})

    def _reorder_categories(self):
        try:
            body = self._read_json_body()
            order = body.get("order")
            if not isinstance(order, list) or not order:
                raise ValueError("invalid payload")
            order = [str(x) for x in order]
        except Exception:
            self._json(400, {"ok": False, "error": "invalid json"})
            return

        try:
            data = load_data()
            cats = data.get("categories") or []
            by_id = {c.get("id"): c for c in cats if c.get("id")}
            next_cats = []
            seen = set()
            for i, cat_id in enumerate(order, start=1):
                cat = by_id.get(cat_id)
                if not cat or cat_id in seen:
                    continue
                cat = dict(cat)
                cat["order"] = i
                next_cats.append(cat)
                seen.add(cat_id)
            # Keep any categories missing from payload at the end
            for cat in cats:
                cat_id = cat.get("id")
                if not cat_id or cat_id in seen:
                    continue
                cat = dict(cat)
                cat["order"] = len(next_cats) + 1
                next_cats.append(cat)
                seen.add(cat_id)
            data["categories"] = next_cats
            write_data(data)
            self._json(200, {"ok": True})
        except Exception as exc:
            self._json(500, {"ok": False, "error": str(exc)})

    def _json(self, code: int, obj: dict):
        payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        # Quieter logs: only API + errors
        msg = fmt % args
        if "/api/" in msg or args and str(args[1]).startswith(("4", "5")):
            super().log_message(fmt, *args)


def main():
    if not JSON_PATH.exists():
        raise SystemExit(f"missing {JSON_PATH}")
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print()
    print("  面试复习系统已启动（支持编辑保存到代码文件）")
    print(f"  浏览器打开: http://127.0.0.1:{PORT}/")
    print("  按 Ctrl+C 可停止")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")


if __name__ == "__main__":
    main()
