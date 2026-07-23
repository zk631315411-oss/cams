/* ═══════════════════════════════════════════
   题目审核模式 — review.js（主模块）
   负责：队列列表渲染、筛选、render/destroy 入口
   暴露 window.CamsReview = { render, destroy, showQuestion, hideQuestion }
   单题编辑视图在 review-editor.js 中
   ═══════════════════════════════════════════ */
(function () {
  var U = window.CamsUtils;

  /* ── 内部状态（与 review-editor.js 共享） ── */
  var _state = null;
  var _handlers = null;
  var _sourceInfo = null;
  var _questions = [];

  /* ── 工具函数 ── */
  function text(v) { return U.escapeHtml(String(v == null ? "" : v)); }

  function byId(id) { return document.getElementById(id); }

  function statusLabel(status) {
    if (status === "unconfirmed") return "未审核";
    if (status === "draft") return "草稿";
    if (status === "confirmed") return "已确认";
    return status || "未知";
  }

  function statusClass(status) {
    if (status === "unconfirmed") return "status-unconfirmed";
    if (status === "draft") return "status-draft";
    if (status === "confirmed") return "status-confirmed";
    return "";
  }

  /* ── 3.2.1 数据加载 ── */
  function loadData() {
    return Promise.all([
      fetch("/api/reviews/source-info").then(function (r) {
        if (!r.ok) return null; return r.json();
      }).catch(function () { return null; }),
      fetch("/api/reviews/questions").then(function (r) {
        if (!r.ok) return []; return r.json();
      }).catch(function () { return []; })
    ]).then(function (results) {
      _sourceInfo = results[0];
      _questions = results[1] || [];
      /* 同步到 review-editor.js 的共享状态 */
      if (window.CamsReviewEditor) window.CamsReviewEditor.setQuestions(_questions);
      return true;
    });
  }

  /* ── 3.2.2 队列列表渲染 ── */
  function renderList() {
    var container = byId("reviewList");
    if (!container) return;
    if (!_questions.length) {
      container.innerHTML = "<div class=\"empty-panel\"><p>暂无审核队列</p></div>";
      return;
    }
    var html = _questions.map(function (q) {
      var stem = q.stem_zh || q.stem_en || "";
      var stemShort = U.shortText(stem, 80);
      var okMark = q.machine_ok ? "<span class=\"review-item-ok\" title=\"机器验证通过\">✓</span>" : "";
      return '<button class="review-item" data-qid="' + text(q.question_id) + '">' +
        '<span class="review-item-id">' + text(q.question_id) + "</span>" +
        '<span class="review-item-stem">' + text(stemShort) + "</span>" +
        '<span class="review-item-status ' + statusClass(q.formal_status) + '">' + statusLabel(q.formal_status) + "</span>" +
        okMark +
        "</button>";
    }).join("");
    container.innerHTML = html;
    /* 更新统计 */
    var statsEl = byId("reviewStats");
    if (statsEl) {
      var unconfirmed = _questions.filter(function (q) { return q.formal_status === "unconfirmed" || !q.formal_status; }).length;
      var draft = _questions.filter(function (q) { return q.formal_status === "draft"; }).length;
      var confirmed = _questions.filter(function (q) { return q.formal_status === "confirmed"; }).length;
      statsEl.textContent = "未审核: " + unconfirmed + " | 草稿: " + draft + " | 已确认: " + confirmed;
    }
  }

  /* ── 筛选逻辑 ── */
  function applyFilter() {
    var searchVal = byId("reviewSearch") ? byId("reviewSearch").value : "";
    var statusVal = byId("reviewStatusFilter") ? byId("reviewStatusFilter").value : "";
    var container = byId("reviewList");
    if (!container) return;
    var items = container.querySelectorAll(".review-item");
    var lowerSearch = U.normalizeText(searchVal);
    items.forEach(function (item) {
      var qid = item.getAttribute("data-qid") || "";
      var stem = item.querySelector(".review-item-stem");
      var stemText = stem ? U.normalizeText(stem.textContent) : "";
      var statusEl = item.querySelector(".review-item-status");
      var statusText = statusEl ? statusEl.textContent : "";
      var matchSearch = !lowerSearch ||
        U.normalizeText(qid).indexOf(lowerSearch) >= 0 ||
        stemText.indexOf(lowerSearch) >= 0;
      var matchStatus = !statusVal || statusLabel(statusVal) === statusText;
      item.style.display = matchSearch && matchStatus ? "" : "none";
    });
  }

  /* ── 渲染队列列表视图（初始视图） ── */
  function renderListView() {
    var container = byId("detailContent");
    if (!container) return;
    container.innerHTML =
      '<div class="v7-review">' +
      '<div class="review-toolbar">' +
      '<span class="review-stats" id="reviewStats">加载中...</span>' +
      '<a class="review-matrix-link" id="reviewMatrixLink">查看映射表</a>' +
      "</div>" +
      '<div class="review-filter">' +
      '<input type="search" id="reviewSearch" placeholder="搜索题号或题干...">' +
      '<select id="reviewStatusFilter">' +
      '<option value="">全部状态</option>' +
      '<option value="unconfirmed">未审核</option>' +
      '<option value="draft">草稿</option>' +
      '<option value="confirmed">已确认</option>' +
      "</select>" +
      '<button class="review-export-btn" id="reviewExportAll">导出全部</button>' +
      "</div>" +
      '<div class="review-list" id="reviewList"></div>' +
      "</div>";
    renderList();

    /* 绑定筛选事件 */
    var searchInput = byId("reviewSearch");
    var statusFilter = byId("reviewStatusFilter");
    if (searchInput) searchInput.addEventListener("input", applyFilter);
    if (statusFilter) statusFilter.addEventListener("change", applyFilter);

    /* 绑定列表项点击 → 委托到 review-editor.js */
    var list = byId("reviewList");
    if (list) list.addEventListener("click", function (e) {
      var item = e.target.closest(".review-item");
      if (item) {
        var qid = item.getAttribute("data-qid");
        if (qid && window.CamsReviewEditor) window.CamsReviewEditor.showQuestion(qid);
      }
    });

    /* 映射表链接 */
    var matrixLink = byId("reviewMatrixLink");
    if (matrixLink) matrixLink.addEventListener("click", function (e) {
      e.preventDefault();
      if (window.CamsApp && window.CamsApp.showMatrix) window.CamsApp.showMatrix();
    });

    /* 导出全部 */
    var exportAllBtn = byId("reviewExportAll");
    if (exportAllBtn) exportAllBtn.addEventListener("click", function () {
      var content = JSON.stringify(_questions, null, 2);
      var blob = new Blob([content], { type: "application/json;charset=utf-8" });
      var url = URL.createObjectURL(blob);
      var a = document.createElement("a");
      a.href = url;
      a.download = "review_questions_all.json";
      a.click();
      URL.revokeObjectURL(url);
    });
  }

  /* ── render 入口 ── */
  function render(state, handlers) {
    _state = state;
    _handlers = handlers;
    /* 把 state/handlers 传到 review-editor.js */
    if (window.CamsReviewEditor) window.CamsReviewEditor.setState(state, handlers);
    renderListView();
    loadData().then(function () {
      renderList();
      applyFilter();
    });
  }

  /* ── destroy ── */
  function destroy() {
    if (window.CamsReviewEditor) window.CamsReviewEditor.destroy();
    _sourceInfo = null;
    _questions = [];
    _state = null;
    _handlers = null;
    var container = byId("detailContent");
    if (container) container.innerHTML = "";
  }

  /* ── 暴露接口 ── */
  window.CamsReview = {
    render: render,
    destroy: destroy,
    showQuestion: function (qid) {
      if (window.CamsReviewEditor) window.CamsReviewEditor.showQuestion(qid);
    },
    hideQuestion: function () {
      if (window.CamsReviewEditor) window.CamsReviewEditor.hideQuestion();
    }
  };
})();