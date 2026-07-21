(function () {
  var U = window.CamsUtils;

  function byId() { return U.byId("detailContent"); }
  function text(value) { return U.escapeHtml(String(value || "")); }
  function labels(items) { return (items || []).map(function (item) { return "<span class=\"v7-tag\">" + text(item) + "</span>"; }).join(""); }
  function unitLink(unitId) { return "<button class=\"v7-link\" data-unit-id=\"" + text(unitId) + "\">" + text(unitId) + "</button>"; }

  function bind(container, handlers) {
    container.onclick = function (event) {
      var unit = event.target.closest("[data-unit-id]");
      var question = event.target.closest("[data-question-id]");
      var home = event.target.closest("[data-home]");
      if (unit) handlers.selectUnit(unit.dataset.unitId, true);
      if (question) handlers.selectQuestion(question.dataset.questionId);
      if (home) handlers.showHome();
    };
  }

  function renderHome(state, handlers) {
    var container = byId();
    if (!container) return;
    container.innerHTML = "";
  }

  function renderUnit(state, unit, handlers) {
    var container = byId();
    var questions = window.CamsStore.getQuestionsForUnit(state, unit.unit_id);
    container.innerHTML = "<section class=\"v7-panel\">" +
      "<nav class=\"v7-breadcrumb\" aria-label=\"当前位置\">" +
      "<button class=\"v7-breadcrumb-link\" data-home>工作台</button>" +
      "<span class=\"v7-breadcrumb-sep\">/</span>" +
      "<span class=\"v7-breadcrumb-current\">教材知识单元</span>" +
      "</nav>" +
      "<button class=\"panel-back\" data-home>返回工作台</button><p class=\"v7-muted\">教材知识单元 " + text(unit.unit_id) + "</p>" +
      "<h2>" + text(unit.zh_display_text || unit.knowledge_zh || unit.en_quote) + "</h2>" +
      "<p class=\"v7-muted\">" + text((unit.heading_context || []).join(" / ")) + "</p>" + labels(unit.risk_flags) +
      "<h3>英文原文</h3><blockquote>" + text(unit.en_quote) + "</blockquote>" +
      (unit.zh_context_full ? "<h3>中文复核上下文</h3><p>" + text(unit.zh_context_full) + "</p>" : "") +
      "<p class=\"v7-meta\">PDF 页 " + text(unit.pdf_page || "未标注") + (unit.printed_page ? " · 印刷页 " + text(unit.printed_page) : "") + "</p>" +
      "<h3>关联已发布题目</h3>" + (questions.length ? "<div class=\"v7-question-list\">" + questions.map(function (question) { return "<button data-question-id=\"" + text(question.question_id) + "\">" + text(question.stem_zh || question.stem_en || question.question_id) + "</button>"; }).join("") + "</div>" : "<p class=\"v7-muted\">该单元当前没有已发布题目证据引用。</p>") +
      "</section>";
    bind(container, handlers);
  }

  function renderEvidenceCards(cards) {
    if (!cards || !cards.length) return "<p class=\"v7-muted\">该选项没有可发布的教材证据。</p>";
    return "<ul class=\"v7-evidence-list\">" + cards.map(function (card) {
      return "<li>" + unitLink(card.unit_id) + " <span>" + text(card.support_type || "") + "</span><p>" + text(card.reason || "") + "</p></li>";
    }).join("") + "</ul>";
  }

  function renderQuestion(state, question, handlers) {
    var container = byId();
    var evidence = window.CamsStore.getEvidence(state, question.question_id);
    var options = Object.keys(question.options || {}).map(function (key) { return "<li><strong>" + text(key) + ".</strong> " + text(question.options[key]) + "</li>"; }).join("");
    /* 从证据中推断所属单元，用于面包屑 */
    var parentUnitId = "";
    var parentUnitLabel = "";
    if (evidence) {
      var cards = (evidence.option_analysis || [])[0] && (evidence.option_analysis[0].evidence_cards || []);
      if (cards && cards.length) {
        parentUnitId = cards[0].unit_id || "";
        var parentUnit = state.unitById[parentUnitId];
        if (parentUnit) parentUnitLabel = parentUnit.zh_display_text || parentUnit.knowledge_zh || parentUnitId;
      }
    }
    var content = "<section class=\"v7-panel\">" +
      "<nav class=\"v7-breadcrumb\" aria-label=\"当前位置\">" +
      "<button class=\"v7-breadcrumb-link\" data-home>工作台</button>" +
      "<span class=\"v7-breadcrumb-sep\">/</span>" +
      (parentUnitId ? "<button class=\"v7-breadcrumb-link\" data-unit-id=\"" + text(parentUnitId) + "\">" + text(parentUnitLabel) + "</button><span class=\"v7-breadcrumb-sep\">/</span>" : "") +
      "<span class=\"v7-breadcrumb-current\">题目</span>" +
      "</nav>" +
      "<button class=\"panel-back\" data-home>返回工作台</button>" +
      "<p class=\"v7-muted\">" + text(question.question_id) + " · " + text(question.publication_status === "published" ? "已发布" : "未发布") + "</p><h2>" + text(question.stem_zh || question.stem_en) + "</h2>" +
      "<ol class=\"v7-options\">" + options + "</ol>" + labels(question.risk_flags);
    if (!evidence || question.publication_status !== "published") {
      content += "<div class=\"v7-warning\"><h3>证据链尚未发布</h3><p>该题未被认为有教材依据。待指定跑批完成、通过发布校验并冻结为 v7 发布包后才会展示证据与解析。</p></div></section>";
      container.innerHTML = content;
      bind(container, handlers);
      return;
    }
    var explanation = evidence.generated_explanation || {};
    content += "<h3>盲判结论</h3><p class=\"v7-answer\">" + text((evidence.predicted_answer || []).join("、") || "未生成") + "</p>" +
      "<h3>参考答案审计</h3><p>参考答案：" + text((question.answer_reference || []).join("、") || "未提供") + "</p>" +
      (evidence.reference_audit && evidence.reference_audit.conflict_messages ? "<p class=\"v7-muted\">" + text(evidence.reference_audit.conflict_messages.join("；")) + "</p>" : "") +
      (explanation.exam_point ? "<h3>考查方向</h3><p>" + text(explanation.exam_point.text) + "</p>" : "") +
      (explanation.core_analysis ? "<h3>核心解析</h3><p>" + text(explanation.core_analysis.text) + "</p>" : "") +
      "<h3>选项证据</h3>" + (evidence.option_analysis || []).map(function (option) {
        return "<article class=\"v7-option-evidence\"><h4>" + text(option.option) + " · " + text(option.judgement) + " <span>" + text(option.evidence_status) + "</span></h4><p>" + text(option.decision_reason) + "</p>" + renderEvidenceCards(option.evidence_cards) + "</article>";
      }).join("") +
      (explanation.easy_mistake ? "<h3>易错提醒</h3><p>" + text(explanation.easy_mistake.text) + "</p>" : "") + "</section>";
    container.innerHTML = content;
    bind(container, handlers);
  }

  function renderWorkflow(mode, handlers) {
    var container = byId();
    if (!container) return;
    var isQuestion = mode === "explain";
    var title = isQuestion ? "新题解析" : "学生答疑";
    var placeholder = isQuestion ? "粘贴题干与选项。v7 新题解析 API 接入后将在此生成可追溯解析。" : "粘贴学生问题或错题情况。v7 学生答疑 API 接入后将在此生成基于教材的答疑草稿。";
    container.innerHTML = "<section class=\"v7-panel\"><button class=\"panel-back\" data-home>返回看书备课</button><p class=\"v7-muted\">教研工作流</p><h2>" + title + "</h2>" +
      "<textarea class=\"workflow-input\" aria-label=\"" + title + "输入\" placeholder=\"" + text(placeholder) + "\"></textarea>" +
      "<button class=\"workflow-submit\" type=\"button\" disabled title=\"等待 v7 API 接入\">等待 v7 API 接入</button>" +
      "<div class=\"v7-warning\"><h3>接口尚未接入</h3><p>该模式与历史导航已保留，但不会调用旧 v6 API，也不会以无教材依据的结果替代正式流程。</p></div></section>";
    bind(container, handlers);
  }

  window.CamsPanel = { renderHome: renderHome, renderUnit: renderUnit, renderQuestion: renderQuestion, renderWorkflow: renderWorkflow };
})();
