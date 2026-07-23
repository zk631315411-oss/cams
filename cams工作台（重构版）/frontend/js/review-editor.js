/* ═══════════════════════════════════════════
   题目审核模式 — review-editor.js（单题编辑子模块）
   负责：单题加载、编辑视图渲染、自动保存、确认弹窗、导出、临时对照窗
   依赖 review.js 设置 _questions 列表
   暴露 window.CamsReviewEditor = { setState, setQuestions, showQuestion, hideQuestion, destroy }
   ═══════════════════════════════════════════ */
(function () {
  var U = window.CamsUtils;

  /* ── 内部状态 ── */
  var _state = null;
  var _handlers = null;
  var _questions = [];
  var _currentId = null;
  var _currentData = null;
  var _saveTimer = null;
  var _saveStatus = "saved";
  var _tempPane = null;

  /* ── 工具函数 ── */
  function text(v) { return U.escapeHtml(String(v == null ? "" : v)); }
  function byId(id) { return document.getElementById(id); }

  function setState(state, handlers) {
    _state = state;
    _handlers = handlers;
  }

  function setQuestions(list) {
    _questions = list || [];
  }

  /* ── 3.2.3 单题编辑视图 ── */
  function showQuestion(questionId) {
    _currentId = questionId;
    fetch("/api/reviews/questions/" + encodeURIComponent(questionId))
      .then(function (r) {
        if (!r.ok) throw new Error("加载题目失败");
        return r.json();
      })
      .then(function (data) {
        _currentData = data;
        renderDetail(data);
      })
      .catch(function (err) {
        var container = byId("detailContent");
        if (container) container.innerHTML = "<div class=\"empty-panel\"><p class=\"error\">" + text(err.message) + "</p></div>";
      });
  }

  function hideQuestion() {
    _currentId = null;
    _currentData = null;
    clearSaveTimer();
    closeTempPane();
    /* 回到列表视图 — 调用 review.js 重新渲染 */
    if (window.CamsReview && window.CamsReview.render) {
      window.CamsReview.render(_state, _handlers);
    }
  }

  function renderDetail(data) {
    var container = byId("detailContent");
    if (!container) return;
    var q = data.question || data;
    var options = q.options || {};
    var optionKeys = Object.keys(options);
    var answerRef = (q.answer_reference || []).join("、") || "未提供";
    var predicted = (data.machine_judgement || {}).predicted_answer || [];
    var machineOk = data.machine_ok;
    var riskFlags = q.risk_flags || [];
    var machineEvidence = (data.machine_judgement || {}).evidence || [];
    var machineExplanation = (data.machine_judgement || {}).explanation || "";
    var formalEvidence = data.formal_evidence || [];
    var formalAnswer = data.formal_answer || [];
    var formalExplanation = data.formal_explanation || "";

    /* 建构选择题答案编辑区 */
    var answerEditors = "";
    var qType = q.type || "unknown";
    if (qType === "single_choice") {
      answerEditors = optionKeys.map(function (key) {
        var checked = formalAnswer.indexOf(key) >= 0 ? "checked" : "";
        return '<label class="review-answer-option"><input type="radio" name="review_answer" value="' + text(key) + '" ' + checked + "> " + text(key) + "</label>";
      }).join("");
    } else if (qType === "multiple_choice") {
      answerEditors = optionKeys.map(function (key) {
        var checked = formalAnswer.indexOf(key) >= 0 ? "checked" : "";
        return '<label class="review-answer-option"><input type="checkbox" name="review_answer" value="' + text(key) + '" ' + checked + "> " + text(key) + "</label>";
      }).join("");
    } else {
      answerEditors = optionKeys.map(function (key) {
        var checked = formalAnswer.indexOf(key) >= 0 ? "checked" : "";
        return '<label class="review-answer-option"><input type="checkbox" name="review_answer" value="' + text(key) + '" ' + checked + "> " + text(key) + " <span class=\"v7-muted\">(未知题型，手动选择)</span></label>";
      }).join("");
    }

    /* 渲染证据标签 */
    function renderEvidenceTags(evList, editable) {
      if (!evList || !evList.length) return "<p class=\"v7-muted\">暂无证据</p>";
      return evList.map(function (ev, idx) {
        var optionTag = ev.option ? '<span class="review-evidence-option">[' + text(ev.option) + "]</span>" : "";
        var deleteBtn = editable ? '<button class="review-evidence-del" data-ev-idx="' + idx + '" title="删除">×</button>' : "";
        var optionSelect = editable ? '<select class="review-evidence-option-select" data-ev-idx="' + idx + '">' + optionKeys.map(function (k) { return '<option value="' + text(k) + '"' + (ev.option === k ? " selected" : "") + ">" + text(k) + "</option>"; }).join("") + "</select>" : "";
        return '<span class="review-evidence-tag" data-unit-id="' + text(ev.unit_id) + '">' +
          optionTag + text(ev.unit_id) +
          optionSelect +
          deleteBtn +
          "</span>";
      }).join("");
    }

    /* 索引，用于查找前后题 */
    var currentIdx = -1;
    _questions.forEach(function (qItem, idx) {
      if (qItem.question_id === data.question_id) currentIdx = idx;
    });

    container.innerHTML =
      '<div class="v7-review review-detail">' +
      /* ── 只读区 ── */
      '<div class="review-section-readonly">' +
      '<div class="review-detail-head">' +
      '<span class="review-item-id">' + text(data.question_id) + "</span>" +
      (machineOk ? '<span class="review-machine-ok">机器验证通过 ✓</span>' : '<span class="review-machine-fail">机器验证未通过</span>') +
      "</div>" +
      '<h2 class="review-stem">' + text(q.stem_zh || q.stem_en || "") + "</h2>" +
      (optionKeys.length ? '<ol class="v7-options">' + optionKeys.map(function (k) { return "<li><strong>" + text(k) + ".</strong> " + text(options[k]) + "</li>"; }).join("") + "</ol>" : "") +
      '<div class="review-meta-tags">' +
      '<span class="pill blue">' + text(qType) + "</span>" +
      riskFlags.map(function (f) { return '<span class="pill amber">' + text(f) + "</span>"; }).join("") +
      "</div>" +
      '<div class="review-field"><span class="review-field-label">官方参考答案，仅作审计参考</span><p class="review-field-value">' + text(answerRef) + "</p></div>" +
      (predicted.length ? '<div class="review-field"><span class="review-field-label">机器盲判</span><p class="review-field-value">' + text(predicted.join("、")) + "</p></div>" : "") +
      (machineExplanation ? '<div class="review-field"><span class="review-field-label">机器解析</span><div class="review-markdown">' + machineExplanation + "</div></div>" : "") +
      (machineEvidence.length ? '<div class="review-field"><span class="review-field-label">机器证据</span><div class="review-evidence-tags">' + renderEvidenceTags(machineEvidence, false) + "</div></div>" : "") +
      "</div>" +
      /* ── 分隔线 ── */
      '<div class="review-divider"></div>' +
      /* ── 编辑区 ── */
      '<div class="review-section-editable">' +
      '<h3 class="review-section-title">编辑审核</h3>' +
      '<div class="review-field"><span class="review-field-label">答案</span><div class="review-answer-group" id="reviewAnswerGroup">' + answerEditors + "</div></div>" +
      '<div class="review-field"><span class="review-field-label">正式解析</span><textarea class="review-editor" id="reviewExplanationEditor" placeholder="输入 Markdown 格式解析...">' + text(formalExplanation) + "</textarea></div>" +
      '<div class="review-field"><span class="review-field-label">正式证据</span>' +
      '<div class="review-evidence-tags" id="reviewFormalEvidence">' + renderEvidenceTags(formalEvidence, true) + "</div>" +
      '<div class="review-evidence-actions">' +
      '<button class="review-evidence-btn" id="reviewEvidenceFromMachine">从机器证据加入</button>' +
      '<div class="review-evidence-search"><input type="text" id="reviewEvidenceSearch" placeholder="输入 unit_id 或关键词搜索"><button class="review-evidence-btn" id="reviewEvidenceSearchBtn">搜索加入</button></div>' +
      "</div></div>" +
      "</div>" +
      /* ── 操作栏 ── */
      '<div class="review-actions">' +
      '<div class="review-nav-buttons">' +
      (currentIdx > 0 ? '<button class="review-nav-btn" id="reviewPrevBtn" data-qid="' + text(_questions[currentIdx - 1].question_id) + '">上一题</button>' : '<button class="review-nav-btn" disabled>上一题</button>') +
      (currentIdx < _questions.length - 1 ? '<button class="review-nav-btn" id="reviewNextBtn" data-qid="' + text(_questions[currentIdx + 1].question_id) + '">下一题</button>' : '<button class="review-nav-btn" disabled>下一题</button>') +
      "</div>" +
      '<div class="review-action-buttons">' +
      '<span class="review-save-status" id="reviewSaveStatus">已保存</span>' +
      '<button class="review-action-btn" id="reviewSaveDraft">保存草稿</button>' +
      '<button class="review-action-btn primary-action" id="reviewConfirm">确认正式版本</button>' +
      "</div>" +
      '<div class="review-export-buttons">' +
      '<button class="review-export-btn" id="reviewCopyBtn">复制</button>' +
      '<button class="review-export-btn" id="reviewExportMdBtn">导出 Markdown</button>' +
      '<button class="review-export-btn" id="reviewExportJsonBtn">导出 JSON</button>' +
      "</div>" +
      "</div>" +
      "</div>";

    bindDetailEvents();
    bindAutoSave();
  }

  /* ── 绑定单题编辑事件 ── */
  function bindDetailEvents() {
    var container = byId("detailContent");
    if (!container) return;

    /* 上一题 / 下一题 */
    var prevBtn = byId("reviewPrevBtn");
    var nextBtn = byId("reviewNextBtn");
    if (prevBtn) prevBtn.addEventListener("click", function () {
      var qid = prevBtn.getAttribute("data-qid");
      if (qid) { clearSaveTimer(); closeTempPane(); showQuestion(qid); }
    });
    if (nextBtn) nextBtn.addEventListener("click", function () {
      var qid = nextBtn.getAttribute("data-qid");
      if (qid) { clearSaveTimer(); closeTempPane(); showQuestion(qid); }
    });

    /* 保存草稿 */
    var saveBtn = byId("reviewSaveDraft");
    if (saveBtn) saveBtn.addEventListener("click", saveDraft);

    /* 确认正式版本 */
    var confirmBtn = byId("reviewConfirm");
    if (confirmBtn) confirmBtn.addEventListener("click", showConfirmModal);

    /* 证据标签点击（打开临时对照窗） */
    container.querySelectorAll(".review-evidence-tag[data-unit-id]").forEach(function (tag) {
      tag.addEventListener("click", function (e) {
        if (e.target.closest(".review-evidence-del") || e.target.closest(".review-evidence-option-select")) return;
        var unitId = tag.getAttribute("data-unit-id");
        if (unitId) openTempPane(unitId);
      });
    });

    /* 证据删除 */
    container.querySelectorAll(".review-evidence-del").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var tag = btn.closest(".review-evidence-tag");
        if (tag) tag.remove();
        markDirty();
      });
    });

    /* 证据所属选项调整 */
    container.querySelectorAll(".review-evidence-option-select").forEach(function (sel) {
      sel.addEventListener("change", function () { markDirty(); });
    });

    /* 从机器证据加入 */
    var fromMachineBtn = byId("reviewEvidenceFromMachine");
    if (fromMachineBtn) fromMachineBtn.addEventListener("click", function () {
      var machineEvidence = (_currentData.machine_judgement || {}).evidence || [];
      var container = byId("reviewFormalEvidence");
      if (!container) return;
      var existing = container.querySelectorAll(".review-evidence-tag");
      var existingIds = {};
      existing.forEach(function (tag) {
        var uid = tag.getAttribute("data-unit-id");
        if (uid) existingIds[uid] = true;
      });
      machineEvidence.forEach(function (ev) {
        if (existingIds[ev.unit_id]) return;
        existingIds[ev.unit_id] = true;
        var optionKeys = Object.keys((_currentData.question || _currentData).options || {});
        var optionSelect = '<select class="review-evidence-option-select">' + optionKeys.map(function (k) { return '<option value="' + text(k) + '">' + text(k) + "</option>"; }).join("") + "</select>";
        var tag = document.createElement("span");
        tag.className = "review-evidence-tag";
        tag.setAttribute("data-unit-id", ev.unit_id);
        tag.innerHTML = (ev.option ? '<span class="review-evidence-option">[' + text(ev.option) + "]</span>" : "") + text(ev.unit_id) + optionSelect + '<button class="review-evidence-del" title="删除">×</button>';
        container.appendChild(tag);
        tag.querySelector(".review-evidence-del").addEventListener("click", function () { tag.remove(); markDirty(); });
        tag.querySelector(".review-evidence-option-select").addEventListener("change", markDirty);
        tag.addEventListener("click", function (e) {
          if (e.target.closest(".review-evidence-del") || e.target.closest(".review-evidence-option-select")) return;
          openTempPane(ev.unit_id);
        });
      });
      markDirty();
    });

    /* 搜索证据加入 */
    var searchBtn = byId("reviewEvidenceSearchBtn");
    var searchInput = byId("reviewEvidenceSearch");
    if (searchBtn && searchInput) {
      searchBtn.addEventListener("click", function () {
        var query = searchInput.value.trim();
        if (!query) return;
        var container = byId("reviewFormalEvidence");
        if (!container) return;
        var existing = container.querySelectorAll(".review-evidence-tag");
        var existingIds = {};
        existing.forEach(function (tag) {
          var uid = tag.getAttribute("data-unit-id");
          if (uid) existingIds[uid] = true;
        });
        if (existingIds[query]) return;
        existingIds[query] = true;
        var optionKeys = Object.keys((_currentData.question || _currentData).options || {});
        var optionSelect = '<select class="review-evidence-option-select">' + optionKeys.map(function (k) { return '<option value="' + text(k) + '">' + text(k) + "</option>"; }).join("") + "</select>";
        var tag = document.createElement("span");
        tag.className = "review-evidence-tag";
        tag.setAttribute("data-unit-id", query);
        tag.innerHTML = text(query) + optionSelect + '<button class="review-evidence-del" title="删除">×</button>';
        container.appendChild(tag);
        tag.querySelector(".review-evidence-del").addEventListener("click", function () { tag.remove(); markDirty(); });
        tag.querySelector(".review-evidence-option-select").addEventListener("change", markDirty);
        tag.addEventListener("click", function (e) {
          if (e.target.closest(".review-evidence-del") || e.target.closest(".review-evidence-option-select")) return;
          openTempPane(query);
        });
        searchInput.value = "";
        markDirty();
      });
    }

    /* 导出按钮 */
    var copyBtn = byId("reviewCopyBtn");
    if (copyBtn) copyBtn.addEventListener("click", function () { exportReview("copy"); });
    var mdBtn = byId("reviewExportMdBtn");
    if (mdBtn) mdBtn.addEventListener("click", function () { exportReview("markdown"); });
    var jsonBtn = byId("reviewExportJsonBtn");
    if (jsonBtn) jsonBtn.addEventListener("click", function () { exportReview("json"); });
  }

  /* ── 标记脏数据，触发自动保存 ── */
  function markDirty() {
    clearSaveTimer();
    setSaveStatus("saving");
    _saveTimer = setTimeout(function () { saveDraft(); }, 3000);
  }

  function clearSaveTimer() {
    if (_saveTimer) { clearTimeout(_saveTimer); _saveTimer = null; }
  }

  function setSaveStatus(status) {
    _saveStatus = status;
    var el = byId("reviewSaveStatus");
    if (!el) return;
    if (status === "saved") { el.textContent = "已保存"; el.className = "review-save-status saved"; }
    else if (status === "saving") { el.textContent = "保存中..."; el.className = "review-save-status saving"; }
    else if (status === "failed") { el.textContent = "保存失败"; el.className = "review-save-status failed"; }
  }

  /* ── 3.2.5 自动保存 ── */
  function bindAutoSave() {
    var editor = byId("reviewExplanationEditor");
    if (editor) editor.addEventListener("input", markDirty);
    var answerGroup = byId("reviewAnswerGroup");
    if (answerGroup) answerGroup.addEventListener("change", markDirty);
    window.addEventListener("beforeunload", function () {
      if (_saveStatus === "saving" && _currentId) saveDraftSync();
    });
  }

  /* ── 保存草稿（异步） ── */
  function saveDraft() {
    if (!_currentId) return;
    var payload = gatherFormData();
    if (!payload) return;
    setSaveStatus("saving");
    fetch("/api/reviews/questions/" + encodeURIComponent(_currentId) + "/draft", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).then(function (r) {
      if (!r.ok) throw new Error("保存失败");
      setSaveStatus("saved");
      return r;
    }).catch(function () { setSaveStatus("failed"); });
  }

  /* 同步保存（beforeunload 用） */
  function saveDraftSync() {
    var payload = gatherFormData();
    if (!payload) return;
    try {
      var xhr = new XMLHttpRequest();
      xhr.open("PUT", "/api/reviews/questions/" + encodeURIComponent(_currentId) + "/draft", false);
      xhr.setRequestHeader("Content-Type", "application/json");
      xhr.send(JSON.stringify(payload));
    } catch (e) { /* 静默失败 */ }
  }

  /* ── 收集表单数据 ── */
  function gatherFormData() {
    var answerGroup = byId("reviewAnswerGroup");
    var explanationEditor = byId("reviewExplanationEditor");
    var formalEvidence = byId("reviewFormalEvidence");
    if (!answerGroup || !explanationEditor || !formalEvidence) return null;
    var answers = [];
    answerGroup.querySelectorAll("input:checked").forEach(function (cb) { answers.push(cb.value); });
    var explanation = explanationEditor.value;
    var evidenceTags = formalEvidence.querySelectorAll(".review-evidence-tag");
    var evidence = [];
    evidenceTags.forEach(function (tag) {
      var unitId = tag.getAttribute("data-unit-id");
      var optionSelect = tag.querySelector(".review-evidence-option-select");
      var option = optionSelect ? optionSelect.value : "";
      if (unitId) evidence.push({ unit_id: unitId, option: option });
    });
    return { answer: answers, explanation: explanation, evidence: evidence };
  }

  /* ── 3.2.6 确认弹窗 ── */
  function showConfirmModal() {
    var overlay = document.createElement("div");
    overlay.className = "review-modal-overlay";
    var data = _currentData;
    var formalAnswer = data.formal_answer || [];
    var currentAnswer = [];
    var answerGroup = byId("reviewAnswerGroup");
    if (answerGroup) {
      answerGroup.querySelectorAll("input:checked").forEach(function (cb) { currentAnswer.push(cb.value); });
    }
    var formalEvidence = data.formal_evidence || [];
    var currentEvidence = [];
    var evidenceContainer = byId("reviewFormalEvidence");
    if (evidenceContainer) {
      evidenceContainer.querySelectorAll(".review-evidence-tag").forEach(function (tag) {
        var unitId = tag.getAttribute("data-unit-id");
        if (unitId) currentEvidence.push(unitId);
      });
    }
    var answerDiff = "答案: " + (formalAnswer.join("、") || "无") + " → " + (currentAnswer.join("、") || "无");
    var explanationDiff = "解析: " + (data.formal_explanation ? "已编辑" : "无") + " → " + (document.getElementById("reviewExplanationEditor") && document.getElementById("reviewExplanationEditor").value ? "已编辑" : "无");
    var added = currentEvidence.filter(function (id) { return !formalEvidence.some(function (ev) { return ev.unit_id === id; }); }).length;
    var removed = formalEvidence.filter(function (ev) { return currentEvidence.indexOf(ev.unit_id) < 0; }).length;
    var evidenceDiff = "证据: +" + added + " 条, -" + removed + " 条";
    var warning = currentEvidence.length === 0 ? '<div class="review-modal-warning">当前正式证据为空，确认后该题将没有教材依据。</div>' : "";

    overlay.innerHTML =
      '<div class="review-modal">' +
      "<h3>确认正式版本</h3>" +
      '<div class="review-modal-changes">' +
      "<p>" + text(answerDiff) + "</p>" +
      "<p>" + text(explanationDiff) + "</p>" +
      "<p>" + text(evidenceDiff) + "</p>" +
      "</div>" +
      warning +
      '<div class="review-modal-actions">' +
      '<button class="review-modal-cancel" id="reviewModalCancel">取消</button>' +
      '<button class="review-modal-confirm" id="reviewModalConfirm">确认</button>' +
      "</div>" +
      "</div>";
    document.body.appendChild(overlay);

    byId("reviewModalCancel").addEventListener("click", function () { overlay.remove(); });
    byId("reviewModalConfirm").addEventListener("click", function () {
      var payload = gatherFormData();
      if (!payload) return;
      fetch("/api/reviews/questions/" + encodeURIComponent(_currentId) + "/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }).then(function (r) {
        if (!r.ok) throw new Error("确认失败");
        overlay.remove();
        /* 更新列表状态 */
        _questions.forEach(function (q) {
          if (q.question_id === _currentId) q.formal_status = "confirmed";
        });
        hideQuestion();
      }).catch(function (err) {
        overlay.querySelector(".review-modal-changes").innerHTML += '<p class="error">' + text(err.message) + "</p>";
      });
    });
  }

  /* ── 3.2.7 导出 ── */
  function exportReview(format) {
    var data = _currentData;
    if (!data) return;
    var q = data.question || data;
    var content = "";
    if (format === "json") {
      content = JSON.stringify(data, null, 2);
    } else if (format === "markdown") {
      content = "## " + (q.question_id || "") + "\n\n";
      content += "### 题干\n" + (q.stem_zh || q.stem_en || "") + "\n\n";
      content += "### 选项\n";
      var opts = q.options || {};
      Object.keys(opts).forEach(function (k) { content += "- " + k + ". " + opts[k] + "\n"; });
      content += "\n### 答案\n" + ((data.formal_answer || []).join("、") || "未设置") + "\n\n";
      content += "### 解析\n" + (data.formal_explanation || "") + "\n\n";
      content += "### 证据\n";
      (data.formal_evidence || []).forEach(function (ev) { content += "- " + ev.unit_id + (ev.option ? " [" + ev.option + "]" : "") + "\n"; });
    } else if (format === "copy") {
      var textarea = document.createElement("textarea");
      textarea.value = JSON.stringify(data, null, 2);
      document.body.appendChild(textarea);
      textarea.select();
      try { document.execCommand("copy"); } catch (e) { /* 降级 */ }
      textarea.remove();
      return;
    }
    if (format === "markdown" || format === "json") {
      var blob = new Blob([content], { type: "text/plain;charset=utf-8" });
      var url = URL.createObjectURL(blob);
      var a = document.createElement("a");
      a.href = url;
      a.download = (q.question_id || "question") + (format === "json" ? ".json" : ".md");
      a.click();
      URL.revokeObjectURL(url);
    }
  }

  /* ── 3.2.4 临时教材对照窗 ── */
  function openTempPane(unitId) {
    closeTempPane();
    var unit = _state && _state.unitById ? _state.unitById[unitId] : null;
    var pane = document.createElement("div");
    pane.id = "reviewTempPane";
    pane.className = "review-temp-pane";
    pane.innerHTML =
      '<div class="temp-pane-head">' +
      '<span class="temp-pane-title">单元 ' + text(unitId) + "</span>" +
      '<button class="temp-pane-close" id="tempPaneClose">×</button>' +
      "</div>" +
      '<div class="temp-pane-body">' +
      (unit ? "<p>章节: " + text((unit.heading_context || []).join(" / ")) + "</p>" : "") +
      (unit ? "<p>中文: " + text(unit.zh_display_text || unit.knowledge_zh || "") + "</p>" : "") +
      (unit ? "<p>英文: " + text(unit.en_quote || "") + "</p>" : "") +
      (unit ? "<p>PDF 页码: " + text(unit.pdf_page || "未标注") + "</p>" : "") +
      (unit && unit.pdf_page ? '<img src="/api/textbook-page?lang=zh&page=' + encodeURIComponent(unit.pdf_page) + '&scale=0.5" alt="教材预览" style="max-width:100%">' : "") +
      "</div>" +
      '<button class="temp-pane-open" id="tempPaneOpen">在主教材打开</button>';
    _tempPane = pane;
    var detailContent = byId("detailContent");
    if (detailContent) detailContent.appendChild(pane);

    byId("tempPaneClose").addEventListener("click", closeTempPane);
    byId("tempPaneOpen").addEventListener("click", function () {
      closeTempPane();
      if (_handlers && _handlers.selectUnit) _handlers.selectUnit(unitId, true);
      hideQuestion();
    });
  }

  function closeTempPane() {
    if (_tempPane) { _tempPane.remove(); _tempPane = null; }
  }

  /* ── destroy ── */
  function destroy() {
    clearSaveTimer();
    closeTempPane();
    _currentId = null;
    _currentData = null;
    _questions = [];
    _saveStatus = "saved";
  }

  /* ── 暴露接口 ── */
  window.CamsReviewEditor = {
    setState: setState,
    setQuestions: setQuestions,
    showQuestion: showQuestion,
    hideQuestion: hideQuestion,
    destroy: destroy
  };
})();