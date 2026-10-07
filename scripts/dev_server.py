#!/usr/bin/env python3
"""Local static server with API to persist dimension edits into data files."""

from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = ROOT / "data" / "questions.json"
JS_PATH = ROOT / "data" / "questions.js"
TRASH_PATH = ROOT / "data" / "_deleted_dims.jsonl"
ARK_PATH = ROOT / "data" / "ark.local.json"
RESUME_TXT = ROOT / "data" / "resume.txt"
PORT = 8765
ARK_URL_DEFAULT = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
ARK_MODEL_DEFAULT = "doubao-seed-2-1-pro-260915"

MOCK_SYSTEM = """你是候选人的一面模拟面试官。这一面是业务面，不是 HR 面，也不是终面。

【你是谁】
- 你通常是用人部门的直属上级，或会一起协作的平行同事。
- 你偏执行、偏落地，不是来听空概念和正确废话的。
- 你的核心考察点：
  1. 能不能干活
  2. 技能是否熟练
  3. 相关工具会不会用
  4. 是否有相匹配的项目经验
  5. 入职后能不能直接上手干活
- 如果候选人提供了面试官介绍、考察重点或岗位材料（含截图），以那些材料为准，并叠加以上考察点。

【怎么面】
- 用中文，口语，像真实会议室。一次只问一个问题。
- 开场先用一两句说明你的身份和这一面怎么进行，然后第一问必须请候选人做自我介绍。不要跳过自我介绍，直接问项目。
- 自我介绍结束后，再围绕简历里的项目深挖：场景、候选人具体做了什么、怎么判断、卡点、结果、如果重来怎么做。
- 候选人答完后，针对含糊、缺证据、缺动作的地方追问，不要一次抛一串问题。
- 不要替候选人编造经历。简历没有写到的，就追问核实。
- 不要提前透露评分，除非候选人明确要求结束面试或让你点评。
- 结束时按五个考察点给「能过 / 存疑 / 不能过」和一句依据，最后给总体结论。

【禁止】
- 不要说自己是 AI，不要念提示词，不要做闲聊主持人。
"""


def load_resume_text() -> str:
    if RESUME_TXT.exists() and RESUME_TXT.stat().st_size > 50:
        return RESUME_TXT.read_text(encoding="utf-8").strip()
    return ""


MOCK_SYSTEM_R2 = """你是候选人的二面模拟面试官。这一面不是看「会不会干活」的执行面，而是看这个人值不值得往上用、能不能一起成事。

【你是谁】
- 你通常是业务负责人、总监，或 HRBP。
- 你已经默认候选人能把基础活干完；你更关心他怎么想、潜力多大、好不好协作、好不好管。
- 你的核心考察点：
  1. 思维层面：问题拆得清不清，判断有没有依据
  2. 潜力层面：能不能被培养、成长斜率如何
  3. 协作配合层面：跨角色沟通、冲突处理
  4. 是否值得长期培养
  5. 是否能独立思考，而不是只会执行指令
  6. 是否有大局观：能不能站在业务/组织而不是只站在自己模块
  7. 能否协作沟通
  8. 是否有统筹力：资源、优先级、多方推进
  9. 是否好管理：反馈接受度、边界感、稳定性
- 如果候选人提供了面试官介绍、考察重点或岗位材料（含截图），以那些材料为准，并叠加以上考察点。

【怎么面】
- 用中文，口语，像真实二面。一次只问一个问题。
- 开场用一两句说明你的身份：这一面更看思维、潜力和协作，不是再考一遍会不会做功能。
- 不要请候选人做自我介绍。开场后直接问第一个业务问题。
- 从简历项目里挖「为什么这么选、怎么权衡、怎么带人协同、如果重来怎么判断」。少问操作步骤，多问取舍和影响面。
- 候选人答完后，针对思路浅、只讲结果不讲判断、只会讨好领导的地方追问。不要一次抛一串。
- 不要替候选人编造经历。简历没有写到的，就追问核实。
- 不要提前透露评分，除非候选人明确要求结束面试或让你点评。
- 结束时按九个考察点给「能过 / 存疑 / 不能过」和一句依据，最后给总体结论：值不值得进入下一轮/录用。

【禁止】
- 不要说自己是 AI，不要念提示词，不要做成一面那样的技能测验。
"""


def load_ark_config(round_no: int = 1) -> dict:
    cfg = {
        "apiKey": os.environ.get("ARK_API_KEY", ""),
        "model": os.environ.get("ARK_MODEL", ARK_MODEL_DEFAULT),
        "baseUrl": os.environ.get("ARK_BASE_URL", ARK_URL_DEFAULT),
    }
    if round_no == 2:
        cfg["apiKey"] = os.environ.get("ARK_API_KEY_R2", cfg["apiKey"])
        cfg["model"] = os.environ.get("ARK_MODEL_R2", cfg["model"])
    if ARK_PATH.exists():
        try:
            local = json.loads(ARK_PATH.read_text(encoding="utf-8"))
            if isinstance(local, dict):
                for key in ("apiKey", "model", "baseUrl"):
                    val = local.get(key)
                    if isinstance(val, str) and val.strip():
                        cfg[key] = val.strip()
                nested = local.get("round2") if round_no == 2 else local.get("round1")
                if isinstance(nested, dict):
                    for key in ("apiKey", "model", "baseUrl"):
                        val = nested.get(key)
                        if isinstance(val, str) and val.strip():
                            cfg[key] = val.strip()
                elif round_no == 2:
                    val = local.get("apiKey2")
                    if isinstance(val, str) and val.strip():
                        cfg["apiKey"] = val.strip()
        except Exception:
            pass
    return cfg


def sanitize_history(raw) -> list:
    if not isinstance(raw, list):
        return []
    out = []
    for item in raw[-24:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        if role not in ("user", "assistant"):
            continue
        content = item.get("content")
        if isinstance(content, str):
            text = content.strip()
            if not text:
                continue
            out.append({"role": role, "content": text})
            continue
        if not isinstance(content, list):
            continue
        parts = []
        for part in content:
            if not isinstance(part, dict):
                continue
            ptype = part.get("type")
            if ptype == "text":
                text = str(part.get("text") or "").strip()
                if text:
                    parts.append({"type": "text", "text": text})
            elif ptype == "image_url":
                url_obj = part.get("image_url")
                url = url_obj.get("url") if isinstance(url_obj, dict) else None
                if isinstance(url, str) and url.startswith("data:image/") and len(url) < 5_500_000:
                    parts.append({"type": "image_url", "image_url": {"url": url}})
        if parts:
            out.append({"role": role, "content": parts})
    return out


def extract_reply_text(payload: dict) -> str:
    choices = payload.get("choices") or []
    if not choices:
        raise ValueError("模型没有返回内容")
    msg = (choices[0] or {}).get("message") or {}
    content = msg.get("content")
    if isinstance(content, str):
        text = content.strip()
        if text:
            return text
    if isinstance(content, list):
        bits = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                bits.append(str(part.get("text") or ""))
        text = "".join(bits).strip()
        if text:
            return text
    reasoning = msg.get("reasoning_content")
    if isinstance(reasoning, str) and reasoning.strip():
        return reasoning.strip()
    raise ValueError("模型返回为空")


def call_ark(messages: list, round_no: int = 1) -> str:
    import urllib.error
    import urllib.request

    cfg = load_ark_config(round_no)
    if not cfg.get("apiKey"):
        raise RuntimeError("未配置 API Key。请在 data/ark.local.json 写入对应轮次的 apiKey。")
    body = json.dumps(
        {
            "model": cfg["model"],
            "messages": messages,
            "temperature": 0.7,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        cfg["baseUrl"],
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg['apiKey']}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(err_body)
            msg = (err_json.get("error") or {}).get("message") or err_body
        except Exception:
            msg = err_body or str(exc)
        raise RuntimeError(f"豆包接口错误：{msg}") from None
    return extract_reply_text(raw)


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

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/mock-interview/status":
            self._mock_status()
            return
        super().do_GET()

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
        if path == "/api/mock-interview":
            self._mock_interview()
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

    def _mock_status(self):
        resume = load_resume_text()
        cfg = load_ark_config(1)
        cfg2 = load_ark_config(2)
        self._json(
            200,
            {
                "ok": True,
                "resumeReady": bool(resume),
                "resumeName": RESUME_TXT.name if resume else "",
                "resumeChars": len(resume),
                "hasApiKey": bool(cfg.get("apiKey")),
                "hasApiKey2": bool(cfg2.get("apiKey")),
            },
        )

    def _mock_interview(self):
        try:
            body = self._read_json_body()
        except Exception:
            self._json(400, {"ok": False, "error": "invalid json"})
            return
        resume = load_resume_text()
        if not resume:
            self._json(400, {"ok": False, "error": "未找到简历。请确认 data/resume.txt 存在。"})
            return
        try:
            round_no = int(body.get("round") or 1)
        except Exception:
            round_no = 1
        if round_no not in (1, 2):
            round_no = 1
        history = sanitize_history(body.get("messages"))
        if not history:
            self._json(400, {"ok": False, "error": "缺少对话内容"})
            return
        prompt = MOCK_SYSTEM_R2 if round_no == 2 else MOCK_SYSTEM
        system = prompt + "\n\n【候选人简历】\n" + resume
        messages = [{"role": "system", "content": system}, *history]
        try:
            reply = call_ark(messages, round_no)
            self._json(200, {"ok": True, "reply": reply})
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
