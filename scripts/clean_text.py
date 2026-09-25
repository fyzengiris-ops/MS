# -*- coding: utf-8 -*-
"""Clean soft line-breaks and structure label: paragraphs in question data."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_JSON = ROOT / "data" / "questions.json"
DATA_JS = ROOT / "data" / "questions.js"

# Line that starts a labeled block: short phrase + fullwidth/halfwidth colon
LABEL_LINE = re.compile(r"^([^\n。！？；;：:]{1,20})([：:])(.*)$")
# Mid-text label after sentence end
MID_LABEL = re.compile(r"([。！？；;])\s*([^\n。！？；;：:]{1,18}[：:])")


def heal_newlines(text: str) -> str:
    """Join PDF soft-wraps; keep breaks before labeled lines."""
    if not text:
        return ""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = []
    for raw in lines:
        s = raw.strip()
        if not s:
            if out and out[-1] != "":
                out.append("")
            continue
        if not out or out[-1] == "":
            out.append(s)
            continue
        prev = out[-1]
        # Numbered title line (1、xxx) → keep break
        if re.match(r"^\d+[、.．]\s*.{1,40}$", prev) and not re.search(r"[。！？：:]$", prev):
            out.append(s)
            continue
        # New labeled section → keep break
        if LABEL_LINE.match(s):
            out.append(s)
            continue
        # Soft wrap: previous line not a finished sentence
        if not re.search(r"[。！？]$", prev):
            out[-1] = prev + s
            continue
        out.append(s)

    # Drop empty lines for now; structure step adds spacing
    return "\n".join(x for x in out if x != "")


def structure_label_blocks(text: str) -> str:
    """Ensure each '标签：' starts its own paragraph block."""
    if not text:
        return ""
    # Split mid-paragraph labels after 。！？；
    text = MID_LABEL.sub(r"\1\n\2", text)
    parts: list[str] = []
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            continue
        m = LABEL_LINE.match(s)
        if m:
            parts.append(f"{m.group(1)}{m.group(2)}{m.group(3).lstrip()}")
        else:
            parts.append(s)
    # Join with blank line before every labeled paragraph except when it's the only/first continuous prose
    blocks: list[str] = []
    for i, p in enumerate(parts):
        if i > 0 and LABEL_LINE.match(p):
            blocks.append("")  # blank line marker
        blocks.append(p)
    # Represent as paragraphs separated by \n\n
    result_lines: list[str] = []
    for b in blocks:
        if b == "":
            if result_lines and result_lines[-1] != "":
                result_lines.append("")
            continue
        result_lines.append(b)
    # Normalize to double-newline separated paragraphs
    paras = []
    buf = []
    for line in result_lines:
        if line == "":
            if buf:
                paras.append("\n".join(buf))
                buf = []
        else:
            buf.append(line)
    if buf:
        paras.append("\n".join(buf))
    return "\n\n".join(paras)


def clean_text(text: str) -> str:
    return structure_label_blocks(heal_newlines(text or ""))


def main() -> None:
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    changed = 0
    for item in data["items"]:
        for dim in item.get("dimensions") or []:
            old = dim.get("detail") or ""
            new = clean_text(old)
            if new != old:
                dim["detail"] = new
                changed += 1
        old_full = item.get("fullText") or ""
        new_full = clean_text(old_full)
        if new_full != old_full:
            item["fullText"] = new_full
            changed += 1

    DATA_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    DATA_JS.write_text(
        "window.QUESTION_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    print(f"updated fields: {changed}")
    # sanity sample Q02
    for item in data["items"]:
        if item["qid"] == "Q02":
            for d in item["dimensions"]:
                if "边界" in d["label"]:
                    print("---", d["label"])
                    print(d["detail"][:200])
                    print("...")


if __name__ == "__main__":
    main()
