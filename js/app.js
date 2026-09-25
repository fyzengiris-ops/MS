(() => {
  const data = window.QUESTION_DATA;
  if (!data) {
    document.body.innerHTML = "<p style='padding:24px'>未加载到题库数据，请确认 data/questions.js 存在。</p>";
    return;
  }

  const MODE_KEY = "interview-prep-mode-v2";
  const SIDEBAR_KEY = "interview-prep-sidebar-v1";

  function normalizeMode(raw) {
    if (raw === "practice" || raw === "open") return "practice";
    return "memory"; // memory | outline | reveal → memory
  }

  const state = {
    categoryId: "all",
    query: "",
    openId: null,
    mode: normalizeMode(localStorage.getItem(MODE_KEY)),
    sidebarCollapsed: localStorage.getItem(SIDEBAR_KEY) === "1",
  };

  const els = {
    appShell: document.getElementById("appShell"),
    metaSub: document.getElementById("metaSub"),
    catNav: document.getElementById("catNav"),
    searchInput: document.getElementById("searchInput"),
    viewTitle: document.getElementById("viewTitle"),
    questionList: document.getElementById("questionList"),
    modeSwitch: document.querySelector(".mode-switch"),
    sidebarCollapse: document.getElementById("sidebarCollapse"),
    sidebarExpand: document.getElementById("sidebarExpand"),
  };

  function applySidebar() {
    els.appShell.classList.toggle("sidebar-collapsed", state.sidebarCollapsed);
    localStorage.setItem(SIDEBAR_KEY, state.sidebarCollapsed ? "1" : "0");
  }

  function setSidebarCollapsed(collapsed) {
    state.sidebarCollapsed = !!collapsed;
    applySidebar();
  }

  // Mobile: prefer collapsed catalog so content gets the first screen
  if (window.matchMedia("(max-width: 860px)").matches && localStorage.getItem(SIDEBAR_KEY) === null) {
    state.sidebarCollapsed = true;
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

  /** Join PDF soft-wraps; keep breaks before short「标签：」lines. */
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

  function formatDetailHtml(text) {
    const paras = structureLabelBlocks(text);
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

  /** Support ⟦关键句⟧ markers from data cleaning. */
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

  function updateModeTabs() {
    els.modeSwitch.querySelectorAll(".mode-tab").forEach((tab) => {
      const active = tab.dataset.mode === state.mode;
      tab.classList.toggle("active", active);
      tab.setAttribute("aria-selected", active ? "true" : "false");
    });
  }

  function setMode(mode) {
    state.mode = mode === "practice" ? "practice" : "memory";
    localStorage.setItem(MODE_KEY, state.mode);
    updateModeTabs();
    renderList({ scrollToId: state.openId });
  }

  function renderDims(item) {
    const dims = item.dimensions || [];
    if (!dims.length) {
      return `<div class="empty">暂无结构化维度，可查看完整原文。</div>`;
    }
    const isPractice = state.mode === "practice";
    const listClass = "dim-list" + (isPractice ? " mode-open" : "");
    const items = dims
      .map((d, i) => {
        const label = cleanDimLabel(d.label) || d.label || `要点 ${i + 1}`;
        const open = isPractice ? "open" : "";
        return `
        <li class="dim-item ${open}" data-idx="${i}">
          <button type="button" class="dim-summary" ${isPractice ? "tabindex='-1'" : ""}>
            <span class="dim-num">${i + 1}</span>
            <span class="dim-label">${escapeHtml(label)}</span>
            <span class="dim-chevron">▼</span>
          </button>
          <div class="dim-body">${formatDetailHtml(d.detail || "")}</div>
        </li>`;
      })
      .join("");
    return `<ol class="${listClass}">${items}</ol>`;
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
    const counts = countsByCat();
    const cats = [{ id: "all", name: "全部问题" }, ...data.categories];
    els.catNav.innerHTML = cats
      .map(
        (c) => `
      <button type="button" class="cat-btn ${state.categoryId === c.id ? "active" : ""}" data-cat="${c.id}">
        <span>${c.name}</span>
        <span class="count">${counts[c.id] || 0}</span>
      </button>`
      )
      .join("");
  }

  function renderList(opts = {}) {
    const { scrollToId = null } = opts;
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
        const tags = (it.tags || [])
          .map((t) => `<span class="tag">${escapeHtml(t)}</span>`)
          .join("");
        return `
        <article class="q-card ${isOpen ? "is-open" : ""}" data-card="${it.id}" style="animation-delay:${Math.min(idx, 12) * 0.03}s">
          <button type="button" class="q-item" data-toggle="${it.id}" aria-expanded="${isOpen}">
            <div class="q-top">
              <span class="qid-badge">${escapeHtml(it.qid)}</span>
              ${tags}
            </div>
            <p class="q-title">${escapeHtml(it.shortTitle || it.title)}</p>
          </button>
          ${isOpen ? renderAnswerBody(it) : ""}
        </article>`;
      })
      .join("");

    updateModeTabs();

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
    state.openId = state.openId === id ? null : id;
    renderList({ scrollToId: state.openId || id });
  }

  els.catNav.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-cat]");
    if (!btn) return;
    state.categoryId = btn.dataset.cat;
    state.openId = null;
    renderCats();
    renderList();
    if (window.matchMedia("(max-width: 860px)").matches) {
      setSidebarCollapsed(true);
    }
  });

  els.searchInput.addEventListener("input", (e) => {
    state.query = e.target.value;
    state.openId = null;
    renderList();
  });

  els.questionList.addEventListener("click", (e) => {
    const toggle = e.target.closest("[data-toggle]");
    if (toggle) {
      toggleQuestion(toggle.dataset.toggle);
      return;
    }

    if (state.mode === "practice") return;
    const dimBtn = e.target.closest(".dim-summary");
    if (dimBtn) {
      dimBtn.closest(".dim-item")?.classList.toggle("open");
    }
  });

  els.modeSwitch.addEventListener("click", (e) => {
    const tab = e.target.closest("[data-mode]");
    if (!tab) return;
    setMode(tab.dataset.mode);
  });

  els.sidebarCollapse.addEventListener("click", () => setSidebarCollapsed(true));
  els.sidebarExpand.addEventListener("click", () => setSidebarCollapsed(false));

  document.addEventListener("keydown", (e) => {
    if (e.target.matches("input, textarea")) return;
    if (e.key === "[" ) setSidebarCollapsed(true);
    if (e.key === "]" ) setSidebarCollapsed(false);
    if (e.key === "Escape" && state.openId) {
      const id = state.openId;
      state.openId = null;
      renderList({ scrollToId: id });
    }
  });

  els.metaSub.textContent = `${data.meta.subtitle} · 共 ${data.items.length} 题`;
  applySidebar();
  renderCats();
  updateModeTabs();
  renderList();
})();
