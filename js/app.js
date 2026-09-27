(() => {
  const data = window.QUESTION_DATA;
  if (!data) {
    document.body.innerHTML = "<p style='padding:24px'>未加载到题库数据，请确认 data/questions.js 存在。</p>";
    return;
  }

  const SIDEBAR_KEY = "interview-prep-sidebar-v1";
  // Clear legacy keys; persistence is now file-based / single review UX.
  try {
    localStorage.removeItem("interview-prep-edits-v1");
    localStorage.removeItem("interview-prep-mode-v2");
  } catch {}

  const state = {
    categoryId: "all",
    query: "",
    openId: null,
    sidebarCollapsed: localStorage.getItem(SIDEBAR_KEY) === "1",
    editing: null, // { itemId, dimIdx, snapshotHtml, dirty }
    saving: false,
    skipCatClick: false,
  };

  const els = {
    appShell: document.getElementById("appShell"),
    metaSub: document.getElementById("metaSub"),
    catNav: document.getElementById("catNav"),
    searchInput: document.getElementById("searchInput"),
    viewTitle: document.getElementById("viewTitle"),
    questionList: document.getElementById("questionList"),
    sidebarCollapse: document.getElementById("sidebarCollapse"),
    sidebarExpand: document.getElementById("sidebarExpand"),
  };

  // Floating highlight control + toast
  const hlBubble = document.createElement("button");
  hlBubble.type = "button";
  hlBubble.className = "hl-bubble";
  hlBubble.hidden = true;
  hlBubble.setAttribute("aria-label", "加底色");
  document.body.appendChild(hlBubble);

  const toastEl = document.createElement("div");
  toastEl.className = "save-toast";
  toastEl.hidden = true;
  document.body.appendChild(toastEl);
  let toastTimer = null;

  const kwBubble = document.createElement("div");
  kwBubble.className = "kw-bubble";
  kwBubble.hidden = true;
  kwBubble.setAttribute("role", "tooltip");
  document.body.appendChild(kwBubble);
  let kwHideTimer = null;

  function showToast(msg, ok = true) {
    toastEl.textContent = msg;
    toastEl.classList.toggle("is-error", !ok);
    toastEl.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toastEl.hidden = true; }, 2200);
  }

  function hideKeywordBubble() {
    clearTimeout(kwHideTimer);
    kwBubble.hidden = true;
    kwBubble.classList.remove("is-empty", "is-structured", "is-below");
    kwBubble.innerHTML = "";
  }

  /**
   * Normalize memoryKeywords into sections:
   * - flat strings → one chip section
   * - { title, points: ["…"] | [{label, text}] } → structured sections
   */
  function normalizeMemoryKeywords(raw) {
    if (!Array.isArray(raw) || !raw.length) return [];

    // Flat string list (e.g. ["运动","跳舞"])
    if (raw.every((x) => typeof x === "string")) {
      const chips = raw.map((x) => String(x || "").trim()).filter(Boolean);
      return chips.length ? [{ title: "", chips }] : [];
    }

    return raw
      .map((block) => {
        if (!block || typeof block !== "object") return null;
        const title = String(block.title || "").trim();
        const pointsRaw = Array.isArray(block.points) ? block.points : [];
        const points = pointsRaw
          .map((p) => {
            if (typeof p === "string") {
              const s = p.trim();
              if (!s) return null;
              const m = s.match(/^([^：:]{1,20})[：:]([\s\S]+)$/);
              if (m) return { label: m[1].trim(), text: m[2].trim() };
              return { label: "", text: s };
            }
            if (p && typeof p === "object") {
              const label = String(p.label || "").trim();
              const text = String(p.text || "").trim();
              if (!label && !text) return null;
              return { label, text };
            }
            return null;
          })
          .filter(Boolean);
        if (!title && !points.length) return null;
        return { title, points };
      })
      .filter(Boolean);
  }

  function renderKeywordBubbleHtml(sections) {
    if (!sections.length) {
      return { html: `<p class="kw-empty">暂无关键词~</p>`, structured: false, empty: true };
    }

    // Simple chip-only (no section titles)
    if (sections.length === 1 && sections[0].chips) {
      return {
        html: `<div class="kw-chips">${sections[0].chips
          .map((k) => `<span class="kw-chip">${escapeHtml(k)}</span>`)
          .join("")}</div>`,
        structured: false,
        empty: false,
      };
    }

    const html = `<div class="kw-sections">${sections
      .map((sec) => {
        const title = sec.title
          ? `<p class="kw-section-title">${escapeHtml(sec.title)}</p>`
          : "";
        const points = (sec.points || [])
          .map((p) => {
            if (p.label) {
              return `<li class="kw-point"><span class="kw-point-label">${escapeHtml(p.label)}</span><span class="kw-point-text">${escapeHtml(p.text)}</span></li>`;
            }
            return `<li class="kw-point"><span class="kw-point-text">${escapeHtml(p.text)}</span></li>`;
          })
          .join("");
        return `<section class="kw-section">${title}<ul class="kw-points">${points}</ul></section>`;
      })
      .join("")}</div>`;

    return { html, structured: true, empty: false };
  }

  function showKeywordBubble(cardEl, item) {
    if (!cardEl || !item || cardEl.classList.contains("is-open")) {
      hideKeywordBubble();
      return;
    }
    clearTimeout(kwHideTimer);
    const sections = normalizeMemoryKeywords(item.memoryKeywords);
    const rendered = renderKeywordBubbleHtml(sections);
    kwBubble.classList.toggle("is-empty", rendered.empty);
    kwBubble.classList.toggle("is-structured", rendered.structured);
    kwBubble.innerHTML = rendered.html;
    kwBubble.hidden = false;

    // Place above card; if overflow top, flip below
    const rect = cardEl.getBoundingClientRect();
    const tip = kwBubble.getBoundingClientRect();
    let left = rect.left + rect.width / 2 - tip.width / 2;
    left = Math.max(12, Math.min(left, window.innerWidth - tip.width - 12));
    let top = rect.top - tip.height - 12;
    const placeBelow = top < 8;
    if (placeBelow) top = rect.bottom + 12;
    kwBubble.classList.toggle("is-below", placeBelow);
    kwBubble.style.left = `${left + window.scrollX}px`;
    kwBubble.style.top = `${top + window.scrollY}px`;
  }

  const ICON_ADD = `<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M4 19.5V5.2c0-.7.6-1.2 1.2-1.2H14l6 6v9.5c0 .7-.6 1.2-1.2 1.2H5.2c-.7 0-1.2-.5-1.2-1.2zm9-13.3v4.3h4.3L13 6.2zM7.2 14.2h9.6v1.5H7.2v-1.5zm0 3.2h6.4v1.5H7.2V17.4z"/></svg>`;
  const ICON_REMOVE = `<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M4 19.5V5.2c0-.7.6-1.2 1.2-1.2H14l6 6v9.5c0 .7-.6 1.2-1.2 1.2H5.2c-.7 0-1.2-.5-1.2-1.2zm9-13.3v4.3h4.3L13 6.2zM6.3 16.1l1.1-1.1 2.4 2.4 5.3-5.3 1.1 1.1-6.4 6.4-3.5-3.5z"/></svg>`;

  function applySidebar() {
    els.appShell.classList.toggle("sidebar-collapsed", state.sidebarCollapsed);
    localStorage.setItem(SIDEBAR_KEY, state.sidebarCollapsed ? "1" : "0");
  }

  function setSidebarCollapsed(collapsed) {
    state.sidebarCollapsed = !!collapsed;
    applySidebar();
  }

  if (window.matchMedia("(max-width: 860px)").matches && localStorage.getItem(SIDEBAR_KEY) === null) {
    state.sidebarCollapsed = true;
  }

  function sortCategoriesInPlace() {
    data.categories.sort((a, b) => (Number(a.order) || 0) - (Number(b.order) || 0));
  }

  function catName(id) {
    if (id === "all") return "全部问题";
    return data.categories.find((c) => c.id === id)?.name || id;
  }

  function filteredItems() {
    const q = state.query.trim().toLowerCase();
    return data.items.filter((item) => {
      if (state.categoryId !== "all" && item.categoryId !== state.categoryId) return false;
      if (!q) return true;
      const hay = `${item.qid} ${item.title} ${item.shortTitle} ${(item.tags || []).join(" ")} ${item.fullText}`.toLowerCase();
      return hay.includes(q);
    });
  }

  function countsByCat() {
    const map = { all: data.items.length };
    data.categories.forEach((c) => { map[c.id] = 0; });
    data.items.forEach((it) => {
      map[it.categoryId] = (map[it.categoryId] || 0) + 1;
    });
    return map;
  }

  function escapeHtml(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function cleanDimLabel(label) {
    return String(label ?? "")
      .trim()
      .replace(/^(?:\d+(?:\.\d+)*[、.．]\s*|第[一二三四五六七八九十百]+[：:、．.]?\s*)+/u, "")
      .replace(/^[：:、.\-\s]+/u, "")
      .trim();
  }

  function healNewlines(text) {
    const lines = String(text || "").replace(/\r\n?/g, "\n").split("\n");
    const out = [];
    for (const raw of lines) {
      const s = raw.trim();
      if (!s) {
        if (out.length && out[out.length - 1] !== "") out.push("");
        continue;
      }
      if (!out.length || out[out.length - 1] === "") {
        out.push(s);
        continue;
      }
      const prev = out[out.length - 1];
      if (/^\d+[、.．]\s*.{1,40}$/.test(prev) && !/[。！？：:]$/.test(prev)) {
        out.push(s);
        continue;
      }
      if (/^[^\n。！？；;：:]{1,20}[：:]/.test(s)) {
        out.push(s);
        continue;
      }
      if (!/[。！？]$/.test(prev)) {
        out[out.length - 1] = prev + s;
        continue;
      }
      out.push(s);
    }
    return out.filter((x) => x !== "").join("\n");
  }

  function structureLabelBlocks(text) {
    let t = healNewlines(text);
    t = t.replace(/([。！？；;])\s*([^\n。！？；;：:]{1,18}[：:])/g, "$1\n$2");
    return t
      .split(/\n+/)
      .map((x) => x.trim())
      .filter(Boolean);
  }

  function formatHighlights(text) {
    const raw = String(text || "");
    const parts = [];
    const re = /⟦([\s\S]*?)⟧/g;
    let last = 0;
    let match;
    while ((match = re.exec(raw))) {
      if (match.index > last) {
        parts.push(escapeHtml(raw.slice(last, match.index)));
      }
      parts.push(`<mark class="dim-hl">${escapeHtml(match[1])}</mark>`);
      last = match.index + match[0].length;
    }
    if (last < raw.length) parts.push(escapeHtml(raw.slice(last)));
    return parts.join("");
  }

  function parasToHtml(paras) {
    if (!paras.length) return "";
    return paras
      .map((para) => {
        const m = para.match(/^([^\n。！？；;：:]{1,20})([：:])([\s\S]*)$/);
        const body = m ? m[3] : para;
        const head = m
          ? `<strong class="dim-key">${escapeHtml(m[1] + m[2])}</strong>`
          : "";
        return `<p class="dim-para">${head}${formatHighlights(body)}</p>`;
      })
      .join("");
  }

  function formatDetailHtml(text) {
    return parasToHtml(structureLabelBlocks(text));
  }

  function formatDetailHtmlPreserved(text) {
    const paras = String(text || "")
      .replace(/\r\n?/g, "\n")
      .split(/\n+/)
      .map((x) => x.trim())
      .filter(Boolean);
    return parasToHtml(paras);
  }

  function formatDetailForDim(dim) {
    const text = dim?.detail || "";
    return dim?.preserveBreaks ? formatDetailHtmlPreserved(text) : formatDetailHtml(text);
  }

  function serializeNode(node) {
    let out = "";
    node.childNodes.forEach((child) => {
      if (child.nodeType === Node.TEXT_NODE) {
        out += child.textContent;
        return;
      }
      if (child.nodeType !== Node.ELEMENT_NODE) return;
      const tag = child.tagName;
      if (tag === "BR") {
        out += "\n";
        return;
      }
      if (tag === "MARK" || child.classList?.contains("dim-hl")) {
        out += `⟦${child.textContent}⟧`;
        return;
      }
      out += serializeNode(child);
    });
    return out;
  }

  function serializeDimBody(body) {
    const blocks = [...body.children].filter((el) => {
      const tag = el.tagName;
      return tag === "P" || tag === "DIV" || el.classList?.contains("dim-para");
    });
    if (blocks.length) {
      return blocks
        .map((p) => serializeNode(p).replace(/\s+\n/g, "\n").trim())
        .filter(Boolean)
        .join("\n");
    }
    return serializeNode(body).replace(/\s+\n/g, "\n").trim();
  }

  function findDimContext(el) {
    const item = el?.closest?.(".dim-item");
    const card = el?.closest?.("[data-card]");
    if (!item || !card) return null;
    const dimIdx = Number(item.dataset.idx);
    if (Number.isNaN(dimIdx)) return null;
    return {
      itemEl: item,
      itemId: card.dataset.card,
      dimIdx,
      body: item.querySelector(".dim-body"),
      labelEl: item.querySelector(".dim-label"),
    };
  }

  function getEditingItemEl() {
    if (!state.editing) return null;
    return els.questionList.querySelector(
      `[data-card="${state.editing.itemId}"] .dim-item[data-idx="${state.editing.dimIdx}"]`
    );
  }

  function getEditingBody() {
    return getEditingItemEl()?.querySelector(".dim-body") || null;
  }

  function getEditingLabel() {
    return getEditingItemEl()?.querySelector(".dim-label") || null;
  }

  function normalizeEditedLabel(raw, fallback) {
    const text = String(raw ?? "")
      .replace(/\u00a0/g, " ")
      .replace(/\s+/g, " ")
      .trim();
    return text || String(fallback || "").trim() || "未命名要点";
  }

  function hideHlBubble() {
    hlBubble.hidden = true;
    hlBubble.classList.remove("is-remove");
    hlBubble.style.display = "none";
  }

  /** True only when every character of the selection sits inside .dim-hl */
  function selectionFullyHighlighted(range, body) {
    if (!range || range.collapsed) return false;
    const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        if (!node.nodeValue || !node.nodeValue.length) return NodeFilter.FILTER_REJECT;
        try {
          const r = document.createRange();
          r.selectNodeContents(node);
          // overlap with selection?
          if (r.compareBoundaryPoints(Range.END_TO_START, range) >= 0) return NodeFilter.FILTER_REJECT;
          if (r.compareBoundaryPoints(Range.START_TO_END, range) <= 0) return NodeFilter.FILTER_REJECT;
          return NodeFilter.FILTER_ACCEPT;
        } catch {
          return NodeFilter.FILTER_REJECT;
        }
      },
    });

    let node;
    let sawText = false;
    while ((node = walker.nextNode())) {
      const start = node === range.startContainer ? range.startOffset : 0;
      const end = node === range.endContainer ? range.endOffset : node.nodeValue.length;
      if (end <= start) continue;
      sawText = true;
      const mark = node.parentElement?.closest?.("mark.dim-hl");
      if (!mark || !body.contains(mark)) return false;
    }
    return sawText;
  }

  function updateHlBubble() {
    if (!state.editing) {
      hideHlBubble();
      return;
    }
    const body = getEditingBody();
    if (!body) {
      hideHlBubble();
      return;
    }
    const sel = window.getSelection();
    if (!sel?.rangeCount || sel.isCollapsed) {
      hideHlBubble();
      return;
    }
    const range = sel.getRangeAt(0);
    const node = range.commonAncestorContainer;
    const el = node.nodeType === 1 ? node : node.parentElement;
    if (!el || !body.contains(el)) {
      hideHlBubble();
      return;
    }
    if (!String(sel).trim()) {
      hideHlBubble();
      return;
    }

    const remove = selectionFullyHighlighted(range, body);
    hlBubble.classList.toggle("is-remove", remove);
    hlBubble.setAttribute("aria-label", remove ? "取消底色" : "加底色");
    hlBubble.title = remove ? "取消底色" : "加底色";
    hlBubble.innerHTML = remove ? ICON_REMOVE : ICON_ADD;

    const rect = range.getBoundingClientRect();
    if (!rect.width && !rect.height) {
      hideHlBubble();
      return;
    }
    const top = window.scrollY + rect.top - 40;
    const left = window.scrollX + rect.left + rect.width / 2;
    hlBubble.style.top = `${Math.max(8, top)}px`;
    hlBubble.style.left = `${left}px`;
    hlBubble.style.display = "";
    hlBubble.hidden = false;
  }

  function enterEdit(ctx, { focus = true, keepSelection = false, focusTarget = "body" } = {}) {
    if (!ctx?.body) return;
    const labelEl = ctx.labelEl || ctx.itemEl?.querySelector?.(".dim-label");
    if (state.editing && (state.editing.itemId !== ctx.itemId || state.editing.dimIdx !== ctx.dimIdx)) {
      const targetId = ctx.itemId;
      const targetIdx = ctx.dimIdx;
      const wantLabel = focusTarget === "label";
      commitEdit({ reRender: false });
      ctx = findDimContext(
        els.questionList.querySelector(
          `[data-card="${targetId}"] .dim-item[data-idx="${targetIdx}"] .dim-body`
        )
      );
      if (!ctx?.body) return;
      focusTarget = wantLabel ? "label" : "body";
    }
    if (state.editing && state.editing.itemId === ctx.itemId && state.editing.dimIdx === ctx.dimIdx) {
      if (focus) {
        const target = focusTarget === "label" ? ctx.labelEl || labelEl : ctx.body;
        target?.focus();
      }
      return;
    }
    const labelNode = ctx.labelEl || labelEl;
    state.editing = {
      itemId: ctx.itemId,
      dimIdx: ctx.dimIdx,
      snapshotHtml: ctx.body.innerHTML,
      snapshotLabel: labelNode ? labelNode.textContent : "",
      dirty: false,
    };
    ctx.body.contentEditable = "true";
    ctx.body.classList.add("is-editing");
    ctx.body.spellcheck = false;
    if (labelNode) {
      labelNode.contentEditable = "true";
      labelNode.classList.add("is-editing");
      labelNode.spellcheck = false;
      labelNode.setAttribute("title", "编辑标题");
    }
    ctx.itemEl.classList.add("is-editing");
    if (focus) {
      const target = focusTarget === "label" && labelNode ? labelNode : ctx.body;
      target.focus();
      if (!keepSelection || focusTarget === "label") {
        const sel = window.getSelection();
        if (sel) {
          const range = document.createRange();
          range.selectNodeContents(target);
          if (focusTarget !== "label") range.collapse(false);
          sel.removeAllRanges();
          sel.addRange(range);
        }
      }
    }
  }

  function exitEditDom(body, itemEl) {
    hideHlBubble();
    if (body) {
      body.contentEditable = "false";
      body.classList.remove("is-editing");
    }
    const labelEl = itemEl?.querySelector?.(".dim-label");
    if (labelEl) {
      labelEl.contentEditable = "false";
      labelEl.classList.remove("is-editing");
      labelEl.removeAttribute("title");
    }
    itemEl?.classList.remove("is-editing");
  }

  async function saveDimToFiles(itemId, dimIdx, { detail, label }) {
    const item = data.items.find((x) => x.id === itemId);
    if (item?.dimensions?.[dimIdx]) {
      item.dimensions[dimIdx].detail = detail;
      item.dimensions[dimIdx].preserveBreaks = true;
      if (typeof label === "string") {
        item.dimensions[dimIdx].label = label;
        item.dimensions[dimIdx].summary = label;
      }
    }
    try {
      const res = await fetch("/api/save-dim", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ itemId, dimIdx, detail, label }),
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok || !json.ok) {
        throw new Error(json.error || `HTTP ${res.status}`);
      }
      showToast("已保存到代码文件", true);
      return true;
    } catch (err) {
      showToast("保存失败：请用「启动.bat」打开本地服务后再编辑", false);
      console.warn("save-dim failed", err);
      return false;
    }
  }

  async function deleteDimFromFiles(itemId, dimIdx) {
    const item = data.items.find((x) => x.id === itemId);
    if (!item?.dimensions || dimIdx < 0 || dimIdx >= item.dimensions.length) {
      return false;
    }
    const removed = item.dimensions.splice(dimIdx, 1)[0];
    try {
      const res = await fetch("/api/delete-dim", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ itemId, dimIdx }),
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok || !json.ok) {
        // roll back in-memory on failure
        item.dimensions.splice(dimIdx, 0, removed);
        throw new Error(json.error || `HTTP ${res.status}`);
      }
      showToast("已删除面板并保存到代码文件", true);
      return true;
    } catch (err) {
      showToast("删除失败：请用「启动.bat」打开本地服务后再试", false);
      console.warn("delete-dim failed", err);
      return false;
    }
  }

  async function deleteEditingPanel() {
    if (!state.editing || state.saving) return;
    const { itemId, dimIdx } = state.editing;
    const item = data.items.find((x) => x.id === itemId);
    const label = item?.dimensions?.[dimIdx]?.label || `要点 ${dimIdx + 1}`;
    if (!window.confirm(`确认删除整个回答面板「${cleanDimLabel(label) || label}」？\n（会删除标题和正文；若只想改标题，请直接双击标题编辑）`)) {
      return;
    }

    const itemEl = els.questionList.querySelector(
      `[data-card="${itemId}"] .dim-item[data-idx="${dimIdx}"]`
    );
    const body = itemEl?.querySelector(".dim-body");
    state.editing = null;
    exitEditDom(body, itemEl);

    state.saving = true;
    const ok = await deleteDimFromFiles(itemId, dimIdx);
    state.saving = false;
    renderList({ scrollToId: itemId });
    return ok;
  }

  async function commitEdit({ reRender = true } = {}) {
    if (!state.editing || state.saving) return false;
    const { itemId, dimIdx, snapshotHtml, snapshotLabel } = state.editing;
    const itemEl = els.questionList.querySelector(
      `[data-card="${itemId}"] .dim-item[data-idx="${dimIdx}"]`
    );
    const body = itemEl?.querySelector(".dim-body");
    const labelEl = itemEl?.querySelector(".dim-label");
    if (!body) {
      state.editing = null;
      hideHlBubble();
      return false;
    }
    const detail = serializeDimBody(body);
    const nextLabel = normalizeEditedLabel(labelEl?.textContent, snapshotLabel);
    const bodyChanged = body.innerHTML !== snapshotHtml;
    const labelChanged = nextLabel !== normalizeEditedLabel(snapshotLabel, snapshotLabel);
    state.editing = null;
    exitEditDom(body, itemEl);

    if (bodyChanged || labelChanged) {
      state.saving = true;
      await saveDimToFiles(itemId, dimIdx, { detail, label: nextLabel });
      state.saving = false;
    }

    if (reRender) {
      renderList({ scrollToId: itemId });
    } else {
      if (bodyChanged) body.innerHTML = formatDetailHtmlPreserved(detail);
      if (labelEl && labelChanged) labelEl.textContent = nextLabel;
    }
    return true;
  }

  function cancelEdit() {
    if (!state.editing) return;
    const { itemId, dimIdx, snapshotHtml, snapshotLabel } = state.editing;
    const itemEl = els.questionList.querySelector(
      `[data-card="${itemId}"] .dim-item[data-idx="${dimIdx}"]`
    );
    const body = itemEl?.querySelector(".dim-body");
    const labelEl = itemEl?.querySelector(".dim-label");
    if (body) body.innerHTML = snapshotHtml;
    if (labelEl && snapshotLabel != null) labelEl.textContent = snapshotLabel;
    state.editing = null;
    exitEditDom(body, itemEl);
  }

  function unwrapMark(mark) {
    const parent = mark.parentNode;
    if (!parent) return;
    while (mark.firstChild) parent.insertBefore(mark.firstChild, mark);
    parent.removeChild(mark);
    parent.normalize();
  }

  function applyHighlightFromBubble(forceRemove) {
    const body = getEditingBody();
    if (!body) return;
    const sel = window.getSelection();
    if (!sel?.rangeCount || sel.isCollapsed) return;
    const range = sel.getRangeAt(0);
    const node = range.commonAncestorContainer;
    const el = node.nodeType === 1 ? node : node.parentElement;
    if (!el || !body.contains(el)) return;

    const remove = forceRemove ?? selectionFullyHighlighted(range, body);

    if (remove) {
      // Unwrap all marks that intersect the selection
      const marks = [...body.querySelectorAll("mark.dim-hl")].filter((mark) => {
        try {
          const mr = document.createRange();
          mr.selectNodeContents(mark);
          return !(
            mr.compareBoundaryPoints(Range.END_TO_START, range) >= 0 ||
            mr.compareBoundaryPoints(Range.START_TO_END, range) <= 0
          );
        } catch {
          return false;
        }
      });
      marks.forEach(unwrapMark);
    } else {
      try {
        const mark = document.createElement("mark");
        mark.className = "dim-hl";
        range.surroundContents(mark);
      } catch {
        const frag = range.extractContents();
        const mark = document.createElement("mark");
        mark.className = "dim-hl";
        mark.appendChild(frag);
        mark.querySelectorAll("mark.dim-hl").forEach((inner) => unwrapMark(inner));
        range.insertNode(mark);
        mark.normalize();
      }
    }
    sel.removeAllRanges();
    hideHlBubble();
    if (state.editing) state.editing.dirty = true;
  }

  function renderDims(item) {
    const dims = item.dimensions || [];
    if (!dims.length) {
      return `<div class="empty">暂无结构化维度，可查看完整原文。</div>`;
    }
    const items = dims
      .map((d, i) => {
        const label = cleanDimLabel(d.label) || d.label || `要点 ${i + 1}`;
        return `
        <li class="dim-item open" data-idx="${i}">
          <div class="dim-summary">
            <span class="dim-num">${i + 1}</span>
            <span class="dim-label">${escapeHtml(label)}</span>
            <button type="button" class="dim-delete" data-dim-delete aria-label="删除此面板" title="删除此面板">删除</button>
          </div>
          <div class="dim-body" title="双击进入编辑">${formatDetailForDim(d)}</div>
        </li>`;
      })
      .join("");
    return `<ol class="dim-list mode-open">${items}</ol>`;
  }

  function renderAnswerBody(item) {
    const fullTitle =
      item.shortTitle && item.shortTitle !== item.title
        ? `<p class="answer-full-title">${escapeHtml(item.title)}</p>`
        : "";
    return `
      <div class="q-answer">
        ${fullTitle}
        ${renderDims(item)}
        <details class="full-block">
          <summary>查看完整原文</summary>
          <pre>${escapeHtml(item.fullText || "")}</pre>
        </details>
      </div>`;
  }

  function renderCats() {
    sortCategoriesInPlace();
    const counts = countsByCat();
    const cats = [{ id: "all", name: "全部问题" }, ...data.categories];
    els.catNav.innerHTML = cats
      .map(
        (c) => `
      <button type="button" class="cat-btn ${state.categoryId === c.id ? "active" : ""}" data-cat="${c.id}" ${
          c.id === "all" ? "" : 'title="按住拖动可调整顺序"'
        }>
        <span class="cat-grip" aria-hidden="true">⋮⋮</span>
        <span class="cat-name">${escapeHtml(c.name)}</span>
        <span class="count">${counts[c.id] || 0}</span>
      </button>`
      )
      .join("");
  }

  async function saveCategoryOrder(ids) {
    const byId = Object.fromEntries(data.categories.map((c) => [c.id, c]));
    const next = [];
    ids.forEach((id, i) => {
      const cat = byId[id];
      if (!cat) return;
      cat.order = i + 1;
      next.push(cat);
    });
    data.categories.forEach((cat) => {
      if (ids.includes(cat.id)) return;
      cat.order = next.length + 1;
      next.push(cat);
    });
    data.categories = next;

    try {
      const res = await fetch("/api/reorder-categories", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order: ids }),
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok || !json.ok) {
        throw new Error(json.error || `HTTP ${res.status}`);
      }
      showToast("目录顺序已保存到代码文件", true);
      return true;
    } catch (err) {
      showToast("顺序保存失败：请用「启动.bat」打开本地服务后再试", false);
      console.warn("reorder-categories failed", err);
      return false;
    }
  }

  // Sidebar category drag reorder
  const catDrag = {
    pointerId: null,
    id: null,
    el: null,
    startY: 0,
    active: false,
    moved: false,
  };

  function resetCatDrag() {
    if (catDrag.el) catDrag.el.classList.remove("is-dragging");
    els.catNav.classList.remove("is-reordering");
    catDrag.pointerId = null;
    catDrag.id = null;
    catDrag.el = null;
    catDrag.startY = 0;
    catDrag.active = false;
    catDrag.moved = false;
  }

  function readCategoryOrderFromDom() {
    return [...els.catNav.querySelectorAll(".cat-btn[data-cat]")]
      .map((btn) => btn.dataset.cat)
      .filter((id) => id && id !== "all");
  }

  function placeDraggedCategory(clientY) {
    if (!catDrag.el) return;
    const others = [...els.catNav.querySelectorAll('.cat-btn[data-cat]:not([data-cat="all"])')].filter(
      (btn) => btn !== catDrag.el
    );
    let before = null;
    for (const btn of others) {
      const rect = btn.getBoundingClientRect();
      if (clientY < rect.top + rect.height / 2) {
        before = btn;
        break;
      }
    }
    if (before) els.catNav.insertBefore(catDrag.el, before);
    else els.catNav.appendChild(catDrag.el);
  }

  function renderList(opts = {}) {
    const { scrollToId = null } = opts;
    state.editing = null;
    hideHlBubble();
    hideKeywordBubble();
    const items = filteredItems();

    els.viewTitle.textContent = state.query
      ? `搜索「${state.query}」· ${items.length} 题`
      : `${catName(state.categoryId)} · ${items.length} 题`;

    if (!items.length) {
      els.questionList.classList.remove("has-active");
      els.questionList.innerHTML = `<div class="empty">没有匹配的问题</div>`;
      return;
    }

    if (state.openId && !items.some((x) => x.id === state.openId)) {
      state.openId = null;
    }

    els.questionList.classList.toggle("has-active", !!state.openId);
    els.questionList.innerHTML = items
      .map((it, idx) => {
        const isOpen = state.openId === it.id;
        const hasKw = normalizeMemoryKeywords(it.memoryKeywords).length > 0;
        const tags = (it.tags || [])
          .map((t) => `<span class="tag">${escapeHtml(t)}</span>`)
          .join("");
        return `
        <article class="q-card ${isOpen ? "is-open" : ""} ${hasKw ? "has-kw" : "no-kw"}" data-card="${it.id}" style="animation-delay:${Math.min(idx, 12) * 0.03}s">
          <button type="button" class="q-item" data-toggle="${it.id}" aria-expanded="${isOpen}">
            <div class="q-top">
              <span class="qid-badge">${escapeHtml(it.qid)}</span>
              ${hasKw ? "" : `<span class="kw-flag" title="暂无关键词">待记</span>`}
              ${tags}
            </div>
            <p class="q-title">${escapeHtml(it.shortTitle || it.title)}</p>
          </button>
          ${isOpen ? renderAnswerBody(it) : ""}
        </article>`;
      })
      .join("");

    if (scrollToId) {
      requestAnimationFrame(() => {
        const card = els.questionList.querySelector(`[data-card="${scrollToId}"]`);
        if (card) {
          card.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
      });
    }
  }

  function toggleQuestion(id) {
    if (state.editing) commitEdit({ reRender: false });
    hideKeywordBubble();
    state.openId = state.openId === id ? null : id;
    renderList({ scrollToId: state.openId || id });
  }

  els.catNav.addEventListener("pointerdown", (e) => {
    if (e.button !== 0) return;
    const btn = e.target.closest('.cat-btn[data-cat]:not([data-cat="all"])');
    if (!btn || !els.catNav.contains(btn)) return;
    catDrag.pointerId = e.pointerId;
    catDrag.id = btn.dataset.cat;
    catDrag.el = btn;
    catDrag.startY = e.clientY;
    catDrag.active = false;
    catDrag.moved = false;
    try {
      btn.setPointerCapture(e.pointerId);
    } catch {}
  });

  els.catNav.addEventListener("pointermove", (e) => {
    if (catDrag.pointerId !== e.pointerId || !catDrag.el) return;
    if (!catDrag.active) {
      if (Math.abs(e.clientY - catDrag.startY) < 6) return;
      catDrag.active = true;
      catDrag.moved = true;
      state.skipCatClick = true;
      catDrag.el.classList.add("is-dragging");
      els.catNav.classList.add("is-reordering");
    }
    placeDraggedCategory(e.clientY);
  });

  async function finishCatDrag(e) {
    if (catDrag.pointerId != null && e.pointerId !== catDrag.pointerId) return;
    const moved = catDrag.moved;
    const el = catDrag.el;
    try {
      el?.releasePointerCapture?.(e.pointerId);
    } catch {}
    resetCatDrag();
    if (!moved) return;
    const ids = readCategoryOrderFromDom();
    await saveCategoryOrder(ids);
    renderCats();
  }

  els.catNav.addEventListener("pointerup", finishCatDrag);
  els.catNav.addEventListener("pointercancel", finishCatDrag);

  els.catNav.addEventListener("click", (e) => {
    if (state.skipCatClick) {
      state.skipCatClick = false;
      e.preventDefault();
      e.stopPropagation();
      return;
    }
    const btn = e.target.closest("[data-cat]");
    if (!btn) return;
    if (state.editing) commitEdit({ reRender: false });
    state.categoryId = btn.dataset.cat;
    state.openId = null;
    renderCats();
    renderList();
    if (window.matchMedia("(max-width: 860px)").matches) {
      setSidebarCollapsed(true);
    }
  });

  els.searchInput.addEventListener("input", (e) => {
    if (state.editing) commitEdit({ reRender: false });
    state.query = e.target.value;
    state.openId = null;
    renderList();
  });

  els.questionList.addEventListener("click", (e) => {
    const delBtn = e.target.closest("[data-dim-delete]");
    if (delBtn) {
      e.preventDefault();
      e.stopPropagation();
      const ctx = findDimContext(delBtn);
      if (!ctx) return;
      // Ensure we delete the panel currently being edited (or enter then delete)
      if (!state.editing || state.editing.itemId !== ctx.itemId || state.editing.dimIdx !== ctx.dimIdx) {
        enterEdit(ctx, { focus: false });
      }
      deleteEditingPanel();
      return;
    }

    const toggle = e.target.closest("[data-toggle]");
    if (toggle) {
      toggleQuestion(toggle.dataset.toggle);
    }
  });

  // Keep focus in editor when pressing delete / highlight controls
  els.questionList.addEventListener("mousedown", (e) => {
    if (e.target.closest("[data-dim-delete]")) e.preventDefault();
  });

  // Hover collapsed card → keyword bubble
  els.questionList.addEventListener("pointerover", (e) => {
    const card = e.target.closest(".q-card");
    if (!card || !els.questionList.contains(card)) return;
    if (card.contains(e.relatedTarget)) return;
    if (card.classList.contains("is-open")) {
      hideKeywordBubble();
      return;
    }
    const item = data.items.find((x) => x.id === card.dataset.card);
    showKeywordBubble(card, item);
  });

  els.questionList.addEventListener("pointerout", (e) => {
    const card = e.target.closest(".q-card");
    if (!card || !els.questionList.contains(card)) return;
    if (card.contains(e.relatedTarget)) return;
    // Allow moving onto the bubble itself briefly
    kwHideTimer = setTimeout(() => {
      if (kwBubble.matches(":hover")) return;
      hideKeywordBubble();
    }, 80);
  });

  kwBubble.addEventListener("pointerenter", () => clearTimeout(kwHideTimer));
  kwBubble.addEventListener("pointerleave", () => hideKeywordBubble());

  window.addEventListener("scroll", () => {
    hideKeywordBubble();
  }, true);

  // Double-click panel → enter edit (keep word selection from dblclick)
  els.questionList.addEventListener("dblclick", (e) => {
    if (e.target.closest("[data-dim-delete]")) return;
    const itemEl = e.target.closest(".dim-item");
    if (!itemEl) return;
    e.preventDefault();
    const ctx = findDimContext(itemEl);
    if (!ctx?.body) return;
    const onLabel = !!e.target.closest(".dim-label");
    const onBody = !!e.target.closest(".dim-body");
    enterEdit(ctx, {
      focus: true,
      keepSelection: onBody && !onLabel,
      focusTarget: onLabel ? "label" : "body",
    });
    requestAnimationFrame(updateHlBubble);
  });

  // Blur editable area → save to files
  els.questionList.addEventListener("focusout", (e) => {
    const itemEl = e.target.closest?.(".dim-item.is-editing");
    if (!itemEl) return;
    // Defer so highlight / delete controls can cancel
    setTimeout(() => {
      if (!state.editing) {
        hideHlBubble();
        return;
      }
      if (hlBubble === document.activeElement || hlBubble.contains(document.activeElement)) return;
      const related = document.activeElement;
      if (related && itemEl.contains(related)) return;
      if (related?.closest?.("[data-dim-delete]")) return;
      const still = getEditingItemEl();
      if (still !== itemEl) return;
      hideHlBubble();
      commitEdit({ reRender: true });
    }, 120);
  });

  els.questionList.addEventListener("input", (e) => {
    if (!state.editing) return;
    if (!e.target.closest?.(".dim-body.is-editing") && !e.target.closest?.(".dim-label.is-editing")) return;
    state.editing.dirty = true;
  });

  els.questionList.addEventListener("paste", (e) => {
    const label = e.target.closest?.(".dim-label.is-editing");
    if (!label) return;
    e.preventDefault();
    const text = String(e.clipboardData?.getData("text/plain") || "")
      .replace(/\s+/g, " ")
      .trim();
    document.execCommand("insertText", false, text);
  });

  // Keep title as a single line
  els.questionList.addEventListener("keydown", (e) => {
    const label = e.target.closest?.(".dim-label.is-editing");
    if (label && e.key === "Enter") {
      e.preventDefault();
      label.blur();
      return;
    }
    if (!e.target.closest?.(".dim-body.is-editing") && !label) return;
    if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      cancelEdit();
    }
  });

  els.questionList.addEventListener("keyup", () => {
    if (state.editing) updateHlBubble();
  });

  els.questionList.addEventListener("mouseup", () => {
    if (state.editing) requestAnimationFrame(updateHlBubble);
  });

  document.addEventListener("selectionchange", () => {
    if (state.editing) updateHlBubble();
  });

  // Prevent blur when clicking highlight bubble; apply on click
  hlBubble.addEventListener("mousedown", (e) => {
    e.preventDefault();
  });
  hlBubble.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    const remove = hlBubble.classList.contains("is-remove");
    applyHighlightFromBubble(remove);
  });

  els.sidebarCollapse.addEventListener("click", () => setSidebarCollapsed(true));
  els.sidebarExpand.addEventListener("click", () => setSidebarCollapsed(false));

  document.addEventListener("keydown", (e) => {
    if (e.target.matches("input, textarea") || e.target.closest?.(".dim-body.is-editing")) return;
    if (e.key === "[") setSidebarCollapsed(true);
    if (e.key === "]") setSidebarCollapsed(false);
    if (e.key === "Escape" && state.openId) {
      if (state.editing) {
        cancelEdit();
        return;
      }
      const id = state.openId;
      state.openId = null;
      renderList({ scrollToId: id });
    }
  });

  window.addEventListener("scroll", () => {
    if (state.editing && !hlBubble.hidden) updateHlBubble();
  }, true);

  els.metaSub.textContent = `${data.meta.subtitle} · 共 ${data.items.length} 题`;
  applySidebar();
  renderCats();
  renderList();
})();
