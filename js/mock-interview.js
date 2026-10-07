(() => {
  const MAX_IMAGES = 4;
  const MAX_IMAGE_BYTES = 3 * 1024 * 1024;
  const ROUNDS = {
    1: {
      kicker: "业务一面",
      title: "模拟面试官",
      lead: "模型会读取你的简历，扮演用人部门一面面试官（直属上级或平行同事）。这一面偏执行：看你能不能干活、技能熟不熟、工具会不会、经验匹不匹配、能不能直接上手。",
      hint: "把一面面试官介绍、考察重点、岗位 JD 的截图丢进来，模型会按这些材料调整提问。",
      startLabel: "开始一面",
      chatTitle: "业务一面",
      kickoff: "请开始一面模拟面试。先按面试官身份做简短开场，第一问必须请我做自我介绍，不要直接问项目。一次只问一个问题。",
      ending:
        "请结束面试。按五个考察点给出评价：能否干活、技能是否熟练、工具是否会用、经验是否匹配、能不能直接上手。每点给「能过 / 存疑 / 不能过」和一句依据，最后给总体结论。",
    },
    2: {
      kicker: "业务二面",
      title: "模拟面试官",
      lead: "模型会读取你的简历，扮演业务负责人、总监或 HRBP。这一面不重复考执行细节，重点看思维、潜力、协作配合、是否值得长期培养、能否独立思考、有没有大局观、沟通统筹，以及好不好管理。",
      hint: "把二面面试官介绍、考察重点、岗位材料的截图丢进来，模型会按这些材料调整提问。",
      startLabel: "开始二面",
      chatTitle: "业务二面",
      kickoff: "请开始二面模拟面试。先按业务负责人/总监/HRBP 的身份做简短开场，说明这一面更看思维、潜力和协作。不要请我做自我介绍，开场后直接问第一个问题。一次只问一个问题。",
      ending:
        "请结束面试。按九个考察点给出评价：思维层面、潜力层面、协作配合、是否值得长期培养、能否独立思考、是否有大局观、协作沟通、统筹力、是否好管理。每点给「能过 / 存疑 / 不能过」和一句依据，最后给总体结论。",
    },
  };

  let root = null;
  let roundNo = 1;
  let messages = [];
  let images = [];
  let started = false;
  let loading = false;

  function el(html) {
    const t = document.createElement("template");
    t.innerHTML = html.trim();
    return t.content.firstElementChild;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function textOf(content) {
    if (typeof content === "string") return content;
    if (Array.isArray(content)) {
      return content
        .map((p) => (p && p.type === "text" ? p.text : ""))
        .join("\n")
        .trim();
    }
    return "";
  }

  async function fileToDataUrl(file) {
    if (!/^image\/(png|jpe?g|webp)$/i.test(file.type)) {
      throw new Error("只支持 PNG / JPG / WEBP 截图");
    }
    if (file.size > MAX_IMAGE_BYTES) {
      throw new Error(`${file.name} 超过 3MB`);
    }
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = () => reject(new Error("读取图片失败"));
      reader.readAsDataURL(file);
    });
  }

  function roundMeta() {
    return ROUNDS[roundNo] || ROUNDS[1];
  }

  function renderSetup() {
    const meta = roundMeta();
    return `
      <div class="mock-card">
        <p class="mock-kicker">${meta.kicker}</p>
        <h3 class="mock-h">${meta.title}</h3>
        <p class="mock-lead">${meta.lead}</p>
        <p class="mock-resume" id="mockResumeHint">正在读取简历…</p>
        <label class="mock-label">面试官 / 岗位材料截图（可选，最多 ${MAX_IMAGES} 张）</label>
        <p class="mock-hint">${meta.hint}</p>
        <div class="mock-drop">
          <input id="mockFiles" type="file" accept="image/png,image/jpeg,image/webp" multiple />
          <span>选择或拖入截图</span>
        </div>
        <ul class="mock-thumbs" id="mockThumbs"></ul>
        <label class="mock-label" for="mockNotes">补充说明（可选）</label>
        <textarea id="mockNotes" class="mock-notes" rows="3" placeholder="例如：岗位是 AI 产品经理；面试官是业务负责人；希望多追问自适应学习项目。"></textarea>
        <div class="mock-actions">
          <button type="button" class="btn primary" id="mockStart">${meta.startLabel}</button>
        </div>
        <p class="mock-error" id="mockError" hidden></p>
      </div>`;
  }

  function renderChatShell() {
    const meta = roundMeta();
    return `
      <div class="mock-card mock-chat-card">
        <div class="mock-chat-head">
          <div>
            <p class="mock-kicker">进行中</p>
            <h3 class="mock-h">${meta.chatTitle}</h3>
          </div>
          <div class="mock-actions">
            <button type="button" class="btn ghost" id="mockEnd">结束并点评</button>
            <button type="button" class="btn ghost" id="mockReset">重新开始</button>
          </div>
        </div>
        <div class="mock-thread" id="mockThread"></div>
        <form class="mock-composer" id="mockForm">
          <textarea id="mockInput" rows="3" placeholder="用口语回答，Enter 发送，Shift+Enter 换行"></textarea>
          <button type="submit" class="btn primary" id="mockSend">发送</button>
        </form>
        <p class="mock-error" id="mockError" hidden></p>
      </div>`;
  }

  function drawThumbs() {
    const box = root.querySelector("#mockThumbs");
    if (!box) return;
    box.innerHTML = images
      .map(
        (img, i) => `
        <li>
          <img src="${img.dataUrl}" alt="${escapeHtml(img.name)}" />
          <button type="button" data-del-img="${i}" aria-label="移除">×</button>
        </li>`
      )
      .join("");
  }

  function drawThread() {
    const thread = root.querySelector("#mockThread");
    if (!thread) return;
    thread.innerHTML = messages
      .filter((m, i) => !(i === 0 && m.role === "user"))
      .map((m) => {
        const who = m.role === "assistant" ? "面试官" : "我";
        const cls = m.role === "assistant" ? "is-bot" : "is-me";
        return `<div class="mock-msg ${cls}"><span>${who}</span><div>${escapeHtml(textOf(m.content)).replace(/\n/g, "<br>")}</div></div>`;
      })
      .join("");
    if (loading) {
      thread.insertAdjacentHTML(
        "beforeend",
        `<div class="mock-msg is-bot is-wait"><span>面试官</span><div>正在想下一问…</div></div>`
      );
    }
    thread.scrollTop = thread.scrollHeight;
  }

  function showError(msg) {
    const err = root.querySelector("#mockError");
    if (!err) return;
    err.hidden = !msg;
    err.textContent = msg || "";
  }

  function buildStartUserMessage(notes) {
    const textParts = [
      roundMeta().kickoff,
    ];
    if (notes) textParts.push("候选人补充：" + notes);
    if (images.length) {
      textParts.push("下面是我提供的面试官介绍 / 岗位考察材料截图，请据此调整你的身份和提问重点。");
    }
    const text = textParts.join("\n");
    if (!images.length) return { role: "user", content: text };
    return {
      role: "user",
      content: [
        { type: "text", text },
        ...images.map((img) => ({
          type: "image_url",
          image_url: { url: img.dataUrl },
        })),
      ],
    };
  }

  async function callModel(nextMessages) {
    loading = true;
    drawThread();
    showError("");
    const sendBtn = root.querySelector("#mockSend");
    const startBtn = root.querySelector("#mockStart");
    if (sendBtn) sendBtn.disabled = true;
    if (startBtn) startBtn.disabled = true;
    try {
      const res = await fetch("/api/mock-interview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: nextMessages, round: roundNo }),
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok || !json.ok) {
        throw new Error(json.error || `请求失败 HTTP ${res.status}`);
      }
      messages = nextMessages.concat([{ role: "assistant", content: json.reply }]);
    } catch (err) {
      showError(err.message || "模型调用失败");
      throw err;
    } finally {
      loading = false;
      if (sendBtn) sendBtn.disabled = false;
      if (startBtn) startBtn.disabled = false;
      drawThread();
    }
  }

  async function startInterview() {
    const notes = (root.querySelector("#mockNotes")?.value || "").trim();
    const first = buildStartUserMessage(notes);
    started = true;
    messages = [];
    root.innerHTML = renderChatShell();
    bindChat();
    drawThread();
    try {
      await callModel([first]);
    } catch {
      started = false;
      mountSetup();
      const ta = root.querySelector("#mockNotes");
      if (ta) ta.value = notes;
    }
  }

  async function sendAnswer(text, { ending = false } = {}) {
    const content = ending
      ? roundMeta().ending
      : text;
    const next = messages.concat([{ role: "user", content }]);
    messages = next;
    drawThread();
    await callModel(next);
  }

  function bindSetup() {
    const input = root.querySelector("#mockFiles");
    const drop = root.querySelector(".mock-drop");
    input.addEventListener("change", async () => {
      try {
        for (const file of [...input.files]) {
          if (images.length >= MAX_IMAGES) break;
          images.push({ name: file.name, dataUrl: await fileToDataUrl(file) });
        }
        drawThumbs();
        showError("");
      } catch (err) {
        showError(err.message);
      }
      input.value = "";
    });
    drop.addEventListener("dragover", (e) => {
      e.preventDefault();
      drop.classList.add("is-over");
    });
    drop.addEventListener("dragleave", () => drop.classList.remove("is-over"));
    drop.addEventListener("drop", async (e) => {
      e.preventDefault();
      drop.classList.remove("is-over");
      try {
        for (const file of [...e.dataTransfer.files]) {
          if (images.length >= MAX_IMAGES) break;
          images.push({ name: file.name, dataUrl: await fileToDataUrl(file) });
        }
        drawThumbs();
        showError("");
      } catch (err) {
        showError(err.message);
      }
    });
    root.querySelector("#mockThumbs").addEventListener("click", (e) => {
      const btn = e.target.closest("[data-del-img]");
      if (!btn) return;
      images.splice(Number(btn.dataset.delImg), 1);
      drawThumbs();
    });
    root.querySelector("#mockStart").addEventListener("click", startInterview);
  }

  function bindChat() {
    const form = root.querySelector("#mockForm");
    const input = root.querySelector("#mockInput");
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const text = input.value.trim();
      if (!text || loading) return;
      input.value = "";
      try {
        await sendAnswer(text);
      } catch {}
    });
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        form.requestSubmit();
      }
    });
    root.querySelector("#mockEnd").addEventListener("click", async () => {
      if (loading) return;
      try {
        await sendAnswer("", { ending: true });
      } catch {}
    });
    root.querySelector("#mockReset").addEventListener("click", () => {
      messages = [];
      started = false;
      mountSetup();
    });
  }

  async function loadStatus() {
    const hint = root.querySelector("#mockResumeHint");
    try {
      const res = await fetch("/api/mock-interview/status");
      const json = await res.json();
      if (json.ok && json.resumeReady) {
        hint.textContent = `已载入简历：${json.resumeName || "resume.txt"}（${json.resumeChars} 字）`;
        hint.classList.add("is-ok");
      } else {
        hint.textContent = json.error || "未找到简历，请把简历 PDF 放在项目目录，或把文本放到 data/resume.txt";
        hint.classList.add("is-bad");
      }
    } catch {
      hint.textContent = "本地服务未启动。请用「启动.bat」打开后再进行模拟面试。";
      hint.classList.add("is-bad");
    }
  }

  function mountSetup() {
    root.innerHTML = renderSetup();
    bindSetup();
    drawThumbs();
    loadStatus();
  }

  window.renderMockInterview = function (node, round = 1) {
    root = node;
    roundNo = Number(round) === 2 ? 2 : 1;
    started = false;
    messages = [];
    images = [];
    loading = false;
    mountSetup();
  };
})();
