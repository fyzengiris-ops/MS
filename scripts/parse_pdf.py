# -*- coding: utf-8 -*-
"""Parse 问题1.pdf into structured interview Q&A JSON."""
from __future__ import annotations

import json
import re
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
PDF_PATH = PROJECT / "问题1.pdf"
EXTRACTED = PROJECT / "_extracted.txt"
OUT_JSON = ROOT / "data" / "questions.json"

CATEGORIES = [
    {"id": "core", "name": "核心优势", "qRange": "Q01–Q05", "order": 1},
    {"id": "proj1", "name": "项目1｜课外AI答疑Agent", "qRange": "Q06–Q08", "order": 2},
    {"id": "proj2", "name": "项目2｜自适应学习系统", "qRange": "Q09–Q12", "order": 3},
    {"id": "proj3", "name": "项目3｜直播课堂AI助手", "qRange": "Q13–Q16", "order": 4},
    {"id": "followup", "name": "高频项目追问", "qRange": "Q17–Q18", "order": 5},
    {"id": "ai-tech", "name": "AI技术与工具认知", "qRange": "Q19–Q23", "order": 6},
    {"id": "collab", "name": "协作相关", "qRange": "Q24", "order": 7},
    {"id": "biz", "name": "公司业务延伸", "qRange": "Q25–Q27", "order": 8},
    {"id": "character", "name": "个人品性", "qRange": "Q28", "order": 9},
    {"id": "planning", "name": "个人规划", "qRange": "Q17", "order": 10},
]


def ensure_extracted() -> str:
    if EXTRACTED.exists() and EXTRACTED.stat().st_size > 1000:
        return EXTRACTED.read_text(encoding="utf-8")
    import pymupdf

    doc = pymupdf.open(str(PDF_PATH))
    parts = []
    for i, page in enumerate(doc):
        parts.append(f"===== PAGE {i + 1} =====\n")
        parts.append(page.get_text())
        parts.append("\n")
    text = "".join(parts)
    EXTRACTED.write_text(text, encoding="utf-8")
    return text


def cat_from_text(*parts: str) -> str | None:
    h = " ".join(parts).replace(" ", "")
    rules = [
        ("core", ["核心优势"]),
        ("proj1", ["项目1", "课外AI", "课外Ai", "答疑Agent"]),
        ("proj2", ["项目2", "自适应"]),
        ("proj3", ["项目3", "直播课堂", "直播"]),
        ("followup", ["高频", "挑战项目", "历史系统"]),
        ("ai-tech", ["AI技术", "工具认知"]),
        ("collab", ["协作相关", "协作"]),
        ("biz", ["公司业务"]),
        ("character", ["个人品性", "品性"]),
        ("planning", ["个人规划"]),
    ]
    for cid, keys in rules:
        if any(k.replace(" ", "") in h for k in keys):
            return cid
    return None


def qid_num(qid: str) -> int:
    return int(qid[1:])


def default_cat_for_qid(qid: str) -> str:
    n = qid_num(qid)
    if n <= 5:
        return "core"
    if n <= 8:
        return "proj1"
    if n <= 12:
        return "proj2"
    if n <= 16:
        return "proj3"
    if n <= 18:
        return "followup"
    if n <= 23:
        return "ai-tech"
    if n == 24:
        return "collab"
    if n <= 27:
        return "biz"
    return "character"


def is_skip_page(page: str) -> bool:
    head = page[:200]
    if "目录" in head:
        return True
    if "Presenter name" in page or "www.islide.cc" in page:
        # cover-like slide with almost no Q
        if not re.search(r"^Q\d+", page, re.M):
            return True
    if page.strip() in ("核心优势", "项目1", "项目2", "项目3") or re.fullmatch(
        r"(核心优势|项目\d.*|课外Ai答疑|自适应系统|直播.*)", page.strip()
    ):
        return True
    return False


def extract_title_and_body(rest_lines: list[str]) -> tuple[str, str]:
    """Return (title, body) from lines after Qxx."""
    # Drop leading blank / page-number-only lines
    i = 0
    while i < len(rest_lines) and (
        not rest_lines[i].strip() or re.fullmatch(r"\d{1,3}", rest_lines[i].strip())
    ):
        i += 1
    rest = rest_lines[i:]

    title_lines: list[str] = []
    body_idx = 0
    for j, ln in enumerate(rest):
        s = ln.strip()
        if not s:
            if title_lines:
                body_idx = j + 1
                break
            continue
        if re.fullmatch(r"\d{1,3}", s):
            if title_lines:
                body_idx = j + 1
                break
            continue

        # Body starts: numbered dim, bullet, or section header after we have title
        if title_lines and re.match(r"^(\d+[、\.］\)]|○|●|■|◆)", s):
            body_idx = j
            break

        title_lines.append(s)

        joined = "".join(title_lines)
        # 【xxx】——n、title  style: usually one conceptual title line group
        if "【" in joined and ("——" in joined or "—" in joined):
            # keep collecting short continuation only if next isn't body
            # stop after title-like line that looks complete
            if re.search(r"(项目|提问|问题|介绍|回顾|挑战|归因|验证|边界|能力|场景)[？?]?$", s):
                body_idx = j + 1
                break
            if len(title_lines) >= 2:
                body_idx = j + 1
                break
        # Plain question ending
        if re.search(r"[？?吗呢]$", s) and len(title_lines) <= 2:
            body_idx = j + 1
            break
        if len(title_lines) >= 2 and not s.startswith("【"):
            # likely spilled into body - keep first line only if second looks like body
            if re.match(r"^(阶段|背景|方式|第一|第二|第三|目前|所以|这个|应用)", s):
                title_lines.pop()
                body_idx = j
                break
            if len("".join(title_lines)) > 80:
                title_lines.pop()
                body_idx = j
                break
    else:
        body_idx = len(rest)

    title = " ".join(title_lines).strip()
    # Clean title: if oversized, cut at first body-ish fragment
    if len(title) > 100:
        cut = re.split(r"\s+(?=阶段|背景|方式|第一|目前|所以|这个项目|应用操作)", title, maxsplit=1)
        title = cut[0].strip()
        if len(cut) > 1:
            rest = [cut[1]] + rest[body_idx:]
            body_idx = 0

    body = "\n".join(rest[body_idx:]).strip()
    body = re.sub(r"^\d{1,3}\s*\n", "", body).strip()
    body = re.sub(r"\n\d{1,3}\s*$", "", body).strip()
    return title, body


def parse_dimensions(body: str) -> list[dict]:
    body = re.sub(r"^\d{1,3}\s*\n", "", (body or "").strip()).strip()
    if not body or body in ("详细回答内容待补充", "待补充"):
        return [{"label": "待补充", "summary": "详细回答内容待补充", "detail": body or "详细回答内容待补充"}]

    # Prefer 1、 2、 style
    pattern = re.compile(r"(?=^\d+[、\.]\s*)", re.M)
    chunks = [c.strip() for c in pattern.split(body) if c.strip()]

    if len(chunks) <= 1:
        # 从…来说 / 第一：第二： style (e.g. 个人规划)
        pattern_plan = re.compile(
            r"(?=^(?:从[^：:\n]{2,20}来说|第[一二三四五六七八九十]、?\s*|第一：|第二：|第三：))",
            re.M,
        )
        chunks_plan = [c.strip() for c in pattern_plan.split(body) if c.strip()]
        if len(chunks_plan) > 1:
            dims = []
            for chunk in chunks_plan:
                lines = chunk.split("\n")
                first = lines[0].strip()
                m = re.match(r"^(从[^：:\n]{2,20}来说)[：:]?\s*(.*)$", first)
                if m:
                    label = m.group(1)
                    rest = (m.group(2) + "\n" + "\n".join(lines[1:])).strip()
                    dims.append({"label": label, "summary": label, "detail": rest or chunk})
                    continue
                m2 = re.match(r"^(第[一二三四五六七八九十][：:、]?\s*)(.*)$", first)
                if m2:
                    prefix = m2.group(1).strip()
                    rest_first = m2.group(2).strip().lstrip("：: ")
                    detail = ("\n".join(lines[1:]).strip())
                    if rest_first:
                        detail = (rest_first + ("\n" + detail if detail else "")).strip()
                    if "深化AI" in chunk or "AI产品能力" in chunk:
                        label = "第一：深化AI产品能力"
                    elif "产品价值" in chunk or "商业结果" in chunk:
                        label = "第二：扩大产品价值与商业结果责任"
                    else:
                        label = prefix.rstrip("：:、 ") + ("：" + rest_first[:20] if rest_first and len(rest_first) <= 24 else "")
                        if not label or label.endswith("："):
                            label = prefix.rstrip("：:、 ")
                    dims.append({"label": label, "summary": label, "detail": detail or chunk})
                    continue
                dims.append({"label": "补充", "summary": "补充说明", "detail": chunk})
            cleaned = [d for d in dims if d.get("detail") and not re.fullmatch(r"\d{1,3}", d["detail"].strip())]
            if cleaned:
                return cleaned

        # try ○ section headers
        pattern2 = re.compile(r"(?=^○)", re.M)
        chunks2 = [c.strip() for c in pattern2.split(body) if c.strip()]
        if len(chunks2) > 1:
            chunks = chunks2
        else:
            # keep as single block but split paragraphs for readability
            paras = [p.strip() for p in re.split(r"\n{2,}", body) if p.strip()]
            if len(paras) > 1:
                return [
                    {
                        "label": f"要点 {i + 1}",
                        "summary": (p[:36] + "…") if len(p) > 36 else p,
                        "detail": p,
                    }
                    for i, p in enumerate(paras)
                ]
            return [{"label": "完整回答", "summary": "查看详细表达", "detail": body}]

    dims = []
    for chunk in chunks:
        lines = chunk.split("\n")
        first = lines[0].strip()
        m = re.match(r"^(\d+[、\.]\s*)(.+)$", first)
        if m:
            prefix, rest_first = m.group(1), m.group(2).strip()
            # Short label vs long first-line content
            if len(rest_first) <= 28 or re.match(r"^[^。；]{2,28}$", rest_first):
                label = (prefix + rest_first).strip()
                detail = "\n".join(lines[1:]).strip()
                if not detail:
                    detail = rest_first
                    label = prefix.rstrip("、. ") + "、要点"
                    # better: use rest_first as both
                    label = (prefix + rest_first).strip()
            else:
                # long line: take short head as label
                m2 = re.match(r"^([^，。；：:]{2,24})", rest_first)
                short = m2.group(1) if m2 else rest_first[:20]
                label = (prefix + short).strip()
                remainder = rest_first[len(short) :].lstrip("，。；：: ")
                detail = (remainder + ("\n" + "\n".join(lines[1:]) if len(lines) > 1 else "")).strip()
                if not detail:
                    detail = rest_first
            dims.append({"label": label, "summary": label, "detail": detail or label})
            continue

        m3 = re.match(r"^○\s*(.+)$", first)
        if m3:
            label = m3.group(1).strip()
            if len(label) > 36:
                label = label[:36] + "…"
            detail = "\n".join(lines[1:]).strip() or first
            dims.append({"label": label, "summary": label, "detail": detail})
            continue

        if re.fullmatch(r"\d{1,3}", chunk.strip()):
            continue
        dims.append({"label": "补充", "summary": "补充说明", "detail": chunk})
    # Drop empty / page-number noise
    cleaned = []
    for d in dims:
        detail = (d.get("detail") or "").strip()
        if not detail or re.fullmatch(r"\d{1,3}", detail):
            continue
        if d.get("label") == "补充" and len(detail) <= 2:
            continue
        # Strip text numbering; UI already shows index badges
        label = (d.get("label") or "").strip()
        label = re.sub(
            r"^(?:\d+(?:\.\d+)*[、\.．]\s*|第[一二三四五六七八九十百]+[：:、．.]?\s*)+",
            "",
            label,
        ).strip(" ：:、.-")
        if label:
            d["label"] = label
            d["summary"] = label
        cleaned.append(d)
    return cleaned or [{"label": "完整回答", "summary": "查看详细表达", "detail": body}]


def detect_tags(title: str, body: str) -> list[str]:
    tags = []
    mapping = [
        ("项目回顾", ["个人项目回顾"]),
        ("简历提问", ["简历提问", "简历设问"]),
        ("面试提问", ["面试提问"]),
        ("深度思考", ["深度思考"]),
        ("待补充", ["待补充"]),
    ]
    blob = title + body
    for tag, keys in mapping:
        if any(k in blob for k in keys):
            tags.append(tag)
    return tags


def display_title(title: str) -> str:
    """Strip bracket prefixes for cleaner list display, keep full as subtitle."""
    t = title.strip()
    t = re.sub(r"^【[^】]+】\s*[—\-–]+\s*", "", t)
    return t.strip() or title


def main() -> None:
    text = ensure_extracted()
    pages = [p.strip() for p in re.split(r"===== PAGE \d+ =====\n", text) if p.strip()]

    blocks = []
    for page in pages:
        if is_skip_page(page):
            continue
        lines = [ln.rstrip() for ln in page.split("\n")]
        q_idx = None
        qid = None
        part = None
        for i, ln in enumerate(lines):
            m = re.match(r"^(Q\d+)\s*(?:[·・\.]\s*(\d+)\s*/\s*(\d+))?\s*$", ln.strip())
            if m:
                q_idx = i
                qid = m.group(1)
                if m.group(2):
                    part = f"{m.group(2)}/{m.group(3)}"
                break
        if q_idx is None:
            continue

        header = " ".join(lines[:q_idx]).strip()
        # Skip TOC residue where header contains multiple category names
        if header.count("Q") >= 2 or "目录" in header:
            continue

        title, body = extract_title_and_body(lines[q_idx + 1 :])
        if not title:
            continue
        # Filter garbage from TOC misparse
        if re.search(r"Q\d+\s*[–\-]", title) or title in ("公司业务延伸 Q25–Q27 个人品性",):
            continue
        if body.strip() in ("Q28",) and len(title) < 40:
            continue

        cat = cat_from_text(header, title) or default_cat_for_qid(qid)
        # Title-based overrides when PDF reuses Q numbers across modules
        if "职业规划" in title or "3到5年" in title or "个人规划" in header:
            cat = "planning"
        blocks.append(
            {
                "qid": qid,
                "part": part,
                "categoryId": cat,
                "header": header,
                "title": title,
                "body": body,
            }
        )

    # Merge multi-part same qid+title
    merged: OrderedDict[tuple[str, str], dict] = OrderedDict()
    for b in blocks:
        key = (b["qid"], b["title"])
        if key not in merged:
            merged[key] = {
                "qid": b["qid"],
                "categoryId": b["categoryId"],
                "title": b["title"],
                "bodies": [],
            }
        if b["body"]:
            merged[key]["bodies"].append(b["body"])

    items = []
    for idx, ((qid, title), item) in enumerate(merged.items(), start=1):
        full = "\n\n".join(item["bodies"]).strip()
        dims = parse_dimensions(full)
        short = display_title(title)
        # Deduplicate near-identical Q25/Q26 overview slides: keep longer body
        items.append(
            {
                "id": f"{qid}_{idx}",
                "qid": qid,
                "categoryId": item["categoryId"],
                "title": title,
                "shortTitle": short,
                "tags": detect_tags(title, full),
                "dimensions": dims,
                "fullText": full,
                "_order": idx,
            }
        )

    # Drop shorter duplicate of same shortTitle within same qid
    deduped = []
    seen: dict[tuple[str, str], int] = {}
    for it in items:
        key = (it["qid"], re.sub(r"\s+", "", it["shortTitle"])[:40])
        if key in seen:
            prev = deduped[seen[key]]
            if len(it["fullText"]) > len(prev["fullText"]):
                deduped[seen[key]] = it
            continue
        seen[key] = len(deduped)
        deduped.append(it)
    items = deduped

    # Keep document order (merge order), only soft-group by qid
    items.sort(key=lambda x: (qid_num(x["qid"]), x["_order"]))
    for it in items:
        it.pop("_order", None)

    data = {
        "meta": {
            "title": "AI产品经理面试题练习",
            "subtitle": "简历设问与回答｜本地复习版",
            "hint": "练习时先只看「回答维度」，卡住后再展开详细内容。",
            "source": "问题1.pdf",
            "questionCount": len(items),
        },
        "categories": CATEGORIES,
        "items": items,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Also emit JS for file:// double-click open
    js_path = OUT_JSON.with_suffix(".js")
    js_path.write_text(
        "window.QUESTION_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(items)} items -> {OUT_JSON}")
    print(f"Wrote JS bundle -> {js_path}")
    from collections import Counter

    print(Counter(i["categoryId"] for i in items))


if __name__ == "__main__":
    main()
