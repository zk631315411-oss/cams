(function () {
  var U = window.CamsUtils;

  function normalize(value) { return String(value || "").toLowerCase(); }

  function bind(state, handlers) {
    var input = U.byId("searchInput");
    var box = U.byId("searchResults");
    if (!input || !box) return;
    input.addEventListener("input", function () {
      var query = normalize(input.value).trim();
      if (!query) { box.hidden = true; box.innerHTML = ""; return; }
      var results = [];
      state.units.some(function (unit) {
        var haystack = normalize([unit.unit_id, unit.chapter, unit.heading_context, unit.heading_context_zh, unit.knowledge_zh, unit.knowledge_en, unit.zh_display_text, unit.zh_context_full, unit.en_quote].join(" "));
        if (haystack.indexOf(query) >= 0) results.push({ type: "unit", id: unit.unit_id, label: unit.zh_display_text || unit.knowledge_zh || unit.en_quote });
        return results.length >= 8;
      });
      if (results.length < 8) state.questions.some(function (question) {
        var evidence = state.evidenceByQuestionId[question.question_id] || {};
        var haystack = normalize([question.question_id, question.stem_zh, question.stem_en, Object.values(question.options || {}).join(" "), JSON.stringify(evidence.generated_explanation || {})].join(" "));
        if (haystack.indexOf(query) >= 0) results.push({ type: "question", id: question.question_id, label: question.stem_zh || question.stem_en });
        return results.length >= 8;
      });
      box.innerHTML = results.length ? results.map(function (item) {
        return "<button type=\"button\" data-type=\"" + item.type + "\" data-id=\"" + U.escapeHtml(item.id) + "\"><small>" + (item.type === "unit" ? "教材单元" : "题目") + "</small>" + U.escapeHtml(item.label) + "</button>";
      }).join("") : "<p class=\"search-empty\">未找到匹配内容，试试其他关键词</p>";
      box.hidden = false;
    });
    box.addEventListener("click", function (event) {
      var button = event.target.closest("button[data-id]");
      if (!button) return;
      box.hidden = true;
      input.value = "";
      if (button.dataset.type === "unit") handlers.selectUnit(button.dataset.id, true);
      else handlers.selectQuestion(button.dataset.id);
    });
  }
  window.CamsSearch = { bind: bind };
})();
