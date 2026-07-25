// ==UserScript==
// @name         CAMS题库半自动编辑助手
// @namespace    codex.cams.qbank
// @version      1.0.0
// @description  唯一匹配原题后填入建议题干和选项，人工确认后调用后台原生保存逻辑。
// @match        https://focobeikao.ixunke.cn/manage/education/Q_Bank/edit*
// @grant        none
// @sandbox      raw
// @inject-into  page
// @run-at       document-idle
// ==/UserScript==

(function () {
  "use strict";

  const STORAGE_DATA = "cams-qbank-review-data-v1";
  const STORAGE_PROGRESS = "cams-qbank-review-progress-v1";
  const EXPECTED_QBANK_ID = 138;
  const LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  let dataset = null;
  let current = null;
  let snapshot = null;
  let busy = false;

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  function plain(value) {
    const box = document.createElement("div");
    box.innerHTML = value == null ? "" : String(value);
    return (box.textContent || "")
      .replace(/[\u2018\u2019\uFF07]/g, "'")
      .replace(/[\u201C\u201D]/g, '"')
      .replace(/\s+/g, " ")
      .trim();
  }

  function normalized(value) {
    return plain(value)
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function formatLike(existing, replacement) {
    const text = replacement == null ? "" : String(replacement).trim();
    if (!/<[a-z][\s\S]*>/i.test(existing || "")) return text;
    const box = document.createElement("div");
    box.textContent = text;
    return `<p>${box.innerHTML}</p>`;
  }

  function progress() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_PROGRESS) || "{}");
    } catch (_) {
      return {};
    }
  }

  function setProgress(key, value) {
    const data = progress();
    data[key] = { ...value, at: new Date().toISOString() };
    localStorage.setItem(STORAGE_PROGRESS, JSON.stringify(data));
    refreshStats();
  }

  function proxies() {
    const found = new Set();
    for (const element of document.querySelectorAll("*")) {
      let instance = element.__vueParentComponent;
      while (instance) {
        if (instance.proxy) found.add(instance.proxy);
        instance = instance.parent;
      }
    }
    return [...found];
  }

  function listProxy() {
    return proxies().find(
      (proxy) =>
        Array.isArray(proxy.tableData) &&
        typeof proxy.getTableDataEvent === "function" &&
        typeof proxy.showQuestionModalEvent === "function" &&
        "questionModalId" in proxy
    );
  }

  function editorProxy(questionId) {
    return proxies().find(
      (proxy) =>
        Number(proxy.questionModalId) === Number(questionId) &&
        Array.isArray(proxy.questionOptions) &&
        "questionStem" in proxy &&
        typeof proxy.modalSubEvent === "function"
    );
  }

  async function waitFor(check, timeout = 15000) {
    const started = Date.now();
    while (Date.now() - started < timeout) {
      const result = check();
      if (result) return result;
      await sleep(150);
    }
    throw new Error("等待后台页面响应超时");
  }

  function nextItem() {
    if (!dataset) return null;
    const done = progress();
    return dataset.items.find((item) => item.eligible && !done[item.key]);
  }

  function answerLetters(editor) {
    return editor.questionAnswer
      .filter((value) => Number.isInteger(value) && value >= 0)
      .map((value) => LETTERS[value])
      .join("");
  }

  function validateEditor(editor, item) {
    const errors = [];
    if (normalized(editor.questionStem) !== normalized(item.original.question)) {
      errors.push("后台题干与审核表原题不一致");
    }
    const labels = Object.keys(item.original.options);
    if (editor.questionOptions.length !== labels.length) {
      errors.push(`选项数量不一致：后台${editor.questionOptions.length}，审核表${labels.length}`);
    }
    labels.forEach((label, index) => {
      if (normalized(editor.questionOptions[index]) !== normalized(item.original.options[label])) {
        errors.push(`选项${label}与审核表原文不一致`);
      }
    });
    if (answerLetters(editor) !== item.original.answer) {
      errors.push(`答案不一致：后台${answerLetters(editor)}，审核表${item.original.answer}`);
    }
    return errors;
  }

  async function searchRows(proxy, item) {
    const text = plain(item.original.question);
    const attempts = [text.slice(0, 100), text.slice(0, 70), text.slice(0, 45)];
    for (const keyword of attempts) {
      proxy.chapterId = 0;
      proxy.type = undefined;
      proxy.nature = undefined;
      proxy.selectKindId = undefined;
      proxy.keyword = keyword;
      proxy.tablePage.pageSize = 50;
      proxy.getTableDataEvent(1);
      await waitFor(() => !proxy.tableLoading.spinning, 20000);
      const exact = proxy.tableData.filter(
        (row) => normalized(row.stem) === normalized(item.original.question)
      );
      if (exact.length === 1) return exact;
      if (exact.length > 1) throw new Error("搜索到多个完全相同的题干，已停止以防误改");
    }
    return [];
  }

  async function locateAndFill() {
    if (busy) return;
    if (!dataset) return setStatus("请先载入审核数据", true);
    const item = nextItem();
    if (!item) return setStatus("高置信且有变化的题目已全部处理", false);
    const proxy = listProxy();
    if (!proxy) return setStatus("未找到题目列表组件，请刷新页面后重试", true);
    busy = true;
    updateButtons();
    setStatus(`正在定位 ${item.key}...`, false);
    try {
      const rows = await searchRows(proxy, item);
      if (rows.length !== 1) throw new Error("未找到与原英文题干完全一致的后台题目");
      const row = rows[0];
      proxy.showQuestionModalEvent("edit", row.id, row);
      const editor = await waitFor(() => {
        const candidate = editorProxy(row.id);
        return candidate && !candidate.modalLoading && candidate.questionOptions.length
          ? candidate
          : null;
      }, 20000);
      const errors = validateEditor(editor, item);
      if (errors.length) throw new Error(errors.join("；"));
      snapshot = {
        questionId: row.id,
        stem: editor.questionStem,
        options: [...editor.questionOptions],
      };
      editor.questionStem = formatLike(editor.questionStem, item.proposed.question);
      Object.keys(item.proposed.options).forEach((label, index) => {
        editor.questionOptions[index] = formatLike(
          editor.questionOptions[index],
          item.proposed.options[label]
        );
      });
      current = { item, questionId: row.id };
      setStatus(`${item.key} 已填入，后台ID ${row.id}。请检查后点“确认保存”。`, false);
      document.querySelector(".ant-modal-body")?.scrollTo({ top: 0, behavior: "smooth" });
    } catch (error) {
      current = null;
      snapshot = null;
      setStatus(`${item.key}：${error.message}`, true);
    } finally {
      busy = false;
      updateButtons();
    }
  }

  async function confirmSave() {
    if (busy || !current) return;
    const editor = editorProxy(current.questionId);
    if (!editor) return setStatus("编辑弹窗已关闭，请重新定位该题", true);
    if (!window.confirm(`确认保存 ${current.item.key}？脚本不会改动答案和解析。`)) return;
    busy = true;
    updateButtons();
    setStatus(`正在保存 ${current.item.key}...`, false);
    try {
      editor.modalSubEvent({ preventDefault() {} });
      await waitFor(() => !editor.modal, 20000);
      setProgress(current.item.key, {
        status: "saved",
        backendId: current.questionId,
      });
      const savedKey = current.item.key;
      current = null;
      snapshot = null;
      setStatus(`${savedKey} 已保存。可以继续下一题。`, false);
    } catch (error) {
      setStatus(`保存结果未确认：${error.message}。请在后台核对后再继续。`, true);
    } finally {
      busy = false;
      updateButtons();
    }
  }

  function undoFill() {
    if (!current || !snapshot) return;
    const editor = editorProxy(current.questionId);
    if (!editor) return setStatus("编辑弹窗已关闭，无需撤销", true);
    editor.questionStem = snapshot.stem;
    editor.questionOptions.splice(0, editor.questionOptions.length, ...snapshot.options);
    setStatus(`${current.item.key} 已恢复为填入前内容，尚未保存。`, false);
    current = null;
    snapshot = null;
    updateButtons();
  }

  function skipItem() {
    const item = current?.item || nextItem();
    if (!item) return;
    if (current) undoFill();
    const reason = window.prompt(`跳过 ${item.key} 的原因：`, "需要人工核对");
    if (reason === null) return;
    setProgress(item.key, { status: "skipped", reason });
    setStatus(`${item.key} 已跳过并记录。`, false);
  }

  function exportLog() {
    const blob = new Blob([JSON.stringify(progress(), null, 2)], {
      type: "application/json;charset=utf-8",
    });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `CAMS后台编辑记录_${new Date().toISOString().slice(0, 10)}.json`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  function setStatus(message, error) {
    const node = document.querySelector("#cams-helper-status");
    if (!node) return;
    node.textContent = message;
    node.style.color = error ? "#b42318" : "#344054";
  }

  function refreshStats() {
    const node = document.querySelector("#cams-helper-stats");
    if (!node || !dataset) return;
    const done = progress();
    const eligible = dataset.items.filter((item) => item.eligible);
    const saved = eligible.filter((item) => done[item.key]?.status === "saved").length;
    const skipped = eligible.filter((item) => done[item.key]?.status === "skipped").length;
    node.textContent = `可辅助 ${eligible.length}｜已保存 ${saved}｜已跳过 ${skipped}｜剩余 ${eligible.length - saved - skipped}`;
  }

  function updateButtons() {
    for (const id of ["cams-next", "cams-save", "cams-undo", "cams-skip"]) {
      const button = document.querySelector(`#${id}`);
      if (button) button.disabled = busy || (id === "cams-save" && !current) || (id === "cams-undo" && !current);
    }
  }

  async function loadFile(file) {
    const parsed = JSON.parse(await file.text());
    const qbankId = Number(new URLSearchParams(location.search).get("id"));
    if (parsed.meta?.format !== "cams-qbank-review-v1") throw new Error("不是有效的CAMS审核数据文件");
    if (parsed.meta.qbankId !== EXPECTED_QBANK_ID || qbankId !== EXPECTED_QBANK_ID) {
      throw new Error("题库ID不一致，已停止载入");
    }
    dataset = parsed;
    localStorage.setItem(STORAGE_DATA, JSON.stringify(parsed));
    refreshStats();
    setStatus("数据已载入。默认只处理高置信且有变化的题目。", false);
  }

  function createPanel() {
    const panel = document.createElement("section");
    panel.id = "cams-helper";
    panel.innerHTML = `
      <div class="cams-title">CAMS 半自动编辑</div>
      <label class="cams-file">载入审核数据<input id="cams-file" type="file" accept="application/json,.json"></label>
      <div id="cams-helper-stats" class="cams-stats">尚未载入数据</div>
      <button id="cams-next" class="cams-primary">定位并填入下一题</button>
      <div class="cams-row"><button id="cams-save">确认保存</button><button id="cams-undo">撤销填入</button></div>
      <div class="cams-row"><button id="cams-skip">跳过此题</button><button id="cams-export">导出记录</button></div>
      <div id="cams-helper-status" class="cams-status">脚本不会修改答案和解析，也不会自动删除或追加题目。</div>
    `;
    const style = document.createElement("style");
    style.textContent = `
      #cams-helper{position:fixed;right:18px;bottom:18px;z-index:100000;width:310px;padding:14px;background:#fff;border:1px solid #d0d5dd;border-radius:8px;box-shadow:0 8px 28px rgba(16,24,40,.2);font:14px/1.45 system-ui,sans-serif;color:#101828}
      #cams-helper .cams-title{font-size:16px;font-weight:700;margin-bottom:10px}
      #cams-helper .cams-file{display:block;padding:8px;border:1px dashed #98a2b3;border-radius:6px;cursor:pointer;margin-bottom:8px}
      #cams-helper .cams-file input{display:none}
      #cams-helper .cams-stats{font-size:12px;color:#475467;margin:8px 0}
      #cams-helper button{height:34px;border:1px solid #98a2b3;border-radius:5px;background:#fff;cursor:pointer}
      #cams-helper button:disabled{opacity:.45;cursor:not-allowed}
      #cams-helper .cams-primary{width:100%;background:#1677ff;border-color:#1677ff;color:#fff;font-weight:600}
      #cams-helper .cams-row{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px}
      #cams-helper .cams-status{font-size:12px;margin-top:10px;padding-top:8px;border-top:1px solid #eaecf0;max-height:78px;overflow:auto}
    `;
    document.head.appendChild(style);
    document.body.appendChild(panel);
    panel.querySelector("#cams-file").addEventListener("change", async (event) => {
      try {
        await loadFile(event.target.files[0]);
      } catch (error) {
        setStatus(error.message, true);
      }
    });
    panel.querySelector("#cams-next").addEventListener("click", locateAndFill);
    panel.querySelector("#cams-save").addEventListener("click", confirmSave);
    panel.querySelector("#cams-undo").addEventListener("click", undoFill);
    panel.querySelector("#cams-skip").addEventListener("click", skipItem);
    panel.querySelector("#cams-export").addEventListener("click", exportLog);
    updateButtons();
  }

  function restoreData() {
    try {
      const saved = localStorage.getItem(STORAGE_DATA);
      if (saved) {
        dataset = JSON.parse(saved);
        refreshStats();
        setStatus("已恢复上次载入的数据。", false);
      }
    } catch (_) {
      localStorage.removeItem(STORAGE_DATA);
    }
  }

  createPanel();
  restoreData();
})();
