(function () {
  var U = window.CamsUtils;
  var Store = window.CamsStore;
  var Reader = window.CamsReader;
  var Panel = window.CamsPanel;
  var Search = window.CamsSearch;
  var app = { state: null, workMode: "read", currentView: { type: "home" }, backStack: [], forwardStack: [] };

  function snapshot() { return { workMode: app.workMode, view: Object.assign({}, app.currentView) }; }
  function sameSnapshot(left, right) { return left && right && left.workMode === right.workMode && left.view.type === right.view.type && left.view.id === right.view.id; }
  function handlers() { return { showHome: showHome, selectUnit: selectUnit, selectQuestion: selectQuestion, selectChapter: selectChapter }; }

  function updateNavigation() {
    document.querySelectorAll("[data-work-mode]").forEach(function (button) {
      var active = button.getAttribute("data-work-mode") === app.workMode;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", active ? "true" : "false");
    });
    var back = U.byId("historyBack");
    var forward = U.byId("historyForward");
    if (back) back.disabled = !app.backStack.length;
    if (forward) forward.disabled = !app.forwardStack.length;
  }

  function renderCurrent() {
    if (!app.state) return;
    updateNavigation();
    if (app.workMode === "explain" || app.workMode === "qa") {
      Panel.renderWorkflow(app.workMode, handlers());
      return;
    }
    if (app.currentView.type === "unit") {
      var unit = Store.getUnit(app.state, app.currentView.id);
      if (unit) { Reader.locateUnit(unit); Panel.renderUnit(app.state, unit, handlers()); return; }
    }
    if (app.currentView.type === "question") {
      var question = Store.getQuestion(app.state, app.currentView.id);
      if (question) { Panel.renderQuestion(app.state, question, handlers()); return; }
    }
    Panel.renderHome(app.state, handlers());
  }

  function navigate(workMode, view, record) {
    var next = { workMode: workMode, view: view };
    if (record !== false && !sameSnapshot(snapshot(), next)) {
      app.backStack.push(snapshot());
      app.forwardStack = [];
    }
    app.workMode = workMode;
    app.currentView = view;
    renderCurrent();
  }
  function showHome() { navigate("read", { type: "home" }); }
  function setWorkMode(mode) { navigate(mode || "read", { type: "home" }); }
  function selectUnit(unitId, locate) {
    var unit = Store.getUnit(app.state, unitId);
    if (!unit) return;
    navigate("read", { type: "unit", id: unitId });
    if (locate) Reader.locateUnit(unit);
  }
  function selectQuestion(questionId) {
    if (Store.getQuestion(app.state, questionId)) navigate("read", { type: "question", id: questionId });
  }
  function selectChapter(chapterId) {
    var chapter = app.state.chapters.filter(function (item) { return item.chapter_id === chapterId; })[0];
    if (chapter && chapter.unit_ids.length) selectUnit(chapter.unit_ids[0], true);
  }
  function goBack() {
    if (!app.backStack.length) return;
    var previous = app.backStack.pop();
    app.forwardStack.push(snapshot());
    navigate(previous.workMode, previous.view, false);
  }
  function goForward() {
    if (!app.forwardStack.length) return;
    var next = app.forwardStack.pop();
    app.backStack.push(snapshot());
    navigate(next.workMode, next.view, false);
  }
  function bindChrome() {
    var tocPane = document.querySelector(".toc-pane");
    var toggle = U.byId("tocToggleButton");
    if (tocPane && toggle) toggle.addEventListener("click", function () {
      var collapsed = tocPane.classList.toggle("collapsed");
      toggle.textContent = collapsed ? "›" : "‹";
      toggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
    });
    document.querySelectorAll("[data-language]").forEach(function (button) {
      button.addEventListener("click", function () {
        document.querySelectorAll("[data-language]").forEach(function (item) { item.classList.toggle("active", item === button); });
        Reader.setLanguage(button.getAttribute("data-language"));
      });
    });
    document.querySelectorAll("[data-work-mode]").forEach(function (button) { button.addEventListener("click", function () { setWorkMode(button.getAttribute("data-work-mode")); }); });
    U.byId("historyBack").addEventListener("click", goBack);
    U.byId("historyForward").addEventListener("click", goForward);
  }
  function init() {
    bindChrome();
    var status = U.byId("releaseStatus");
    if (status) status.hidden = true;
    Store.load().then(function (state) {
      app.state = state;
      Reader.render(state, handlers());
      Search.bind(state, handlers());
      renderCurrent();
    }).catch(function (error) {
      var pane = U.byId("detailContent");
      if (pane) pane.innerHTML = "<div class=\"empty-panel\"><h2 class=\"error\">v7 教材包不可用</h2><p>" + U.escapeHtml(error.message) + "</p><button class=\"v7-retry-button\" onclick=\"location.reload()\">重新加载</button></div>";
    });
  }
  window.CamsApp = { init: init, goBack: goBack, goForward: goForward, showHome: showHome, selectUnit: selectUnit, selectQuestion: selectQuestion, setWorkMode: setWorkMode };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
