(function () {
  var U = window.CamsUtils;
  var Store = window.CamsStore;
  var Reader = window.CamsReader;
  var Panel = window.CamsPanel;
  var Search = window.CamsSearch;
  var FB = window.CamsFeedback;

  var app = {
    state: null,
    currentCardId: null,
    selectedEdgeTarget: null,
    currentView: null,
    annotationMode: "priority",
    workMode: "read",
    viewHistory: [],
    visibleNotes: [],
    workflowText: {
      explain: "",
      qa: ""
    },
    workflowState: {
      explain: {
        loading: false,
        error: "",
        draft: null,
        drafts: [],
        draftsLoading: false,
        draftsError: "",
        historyLoadingId: "",
        historyCollapsed: false,
        deletingDraftId: "",
        errorCode: ""
      },
      qa: {
        loading: false,
        error: "",
        draft: null,
        drafts: [],
        draftsLoading: false,
        draftsError: "",
        historyLoadingId: "",
        historyCollapsed: false,
        deletingDraftId: "",
        evidenceExpanded: false,
        errorCode: ""
      }
    }
  };

  function setStatus(text, isError) {
    var status = U.byId("statusText");
    if (!status) return;
    status.textContent = text;
    status.className = isError ? "error" : "";
  }

  function buildApiError(res, payload) {
    payload = payload || {};
    var message = payload.message || payload.error || ("HTTP " + res.status);
    var err = new Error(message);
    err.code = payload.error || "";
    err.status = res.status;
    return err;
  }

  function isSameView(a, b) {
    if (!a || !b) return false;
    return a.type === b.type && a.id === b.id && a.filter === b.filter;
  }

  function cloneView(view) {
    if (!view) return null;
    return {
      type: view.type,
      id: view.id,
      filter: view.filter
    };
  }

  function snapshotCurrentView() {
    if (!app.currentView) return null;
    return {
      view: cloneView(app.currentView),
      currentCardId: app.currentCardId,
      selectedEdgeTarget: app.selectedEdgeTarget,
      workMode: app.workMode
    };
  }

  function getCanGoBack() {
    return app.viewHistory.some(function (entry) {
      return entry && !isSameView(entry.view, app.currentView);
    });
  }

  function rememberCurrentView() {
    var snapshot = snapshotCurrentView();
    if (!snapshot) return;
    var last = app.viewHistory[app.viewHistory.length - 1];
    if (last && isSameView(last.view, snapshot.view)) return;
    app.viewHistory.push(snapshot);
    if (app.viewHistory.length > 20) app.viewHistory.shift();
  }

  function restoreSnapshot(snapshot) {
    if (!snapshot || !snapshot.view) return;
    app.currentCardId = snapshot.currentCardId || null;
    app.selectedEdgeTarget = snapshot.selectedEdgeTarget || null;
    app.workMode = snapshot.workMode || app.workMode;
    app.currentView = cloneView(snapshot.view);
    updateWorkModeButtons();
    renderCurrentView();
  }

  function navigateTo(view, options) {
    if (!app.state || !view || !view.type) return;
    options = options || {};
    if (!options.replace && !isSameView(app.currentView, view)) rememberCurrentView();
    app.currentCardId = view.type === "card" ? view.id : null;
    app.selectedEdgeTarget = options.selectedEdgeTarget || null;
    app.currentView = cloneView(view);
    renderCurrentView();
  }

  function withBack(options) {
    options = options || {};
    options.canGoBack = getCanGoBack();
    return options;
  }

  function renderCurrentConcept() {
    if (!app.currentCardId && app.currentView && app.currentView.id) {
      app.currentCardId = app.currentView.id;
    }
    if (!app.currentCardId) return;
    Panel.render(app.state, app.currentCardId, app.selectedEdgeTarget, handlers, withBack());
  }

  function renderCurrentView() {
    if (!app.currentView) return;
    if (app.currentView.type === "home") {
      Panel.renderWorkbenchHome(app.state, handlers, app.workMode, app.workflowText[app.workMode] || "", app.visibleNotes, app.workflowState[app.workMode] || null);
    } else if (app.currentView.type === "card") {
      renderCurrentConcept();
    } else if (app.currentView.type === "question") {
      Panel.renderQuestionDetail(app.state, app.currentView.id, handlers, withBack());
    } else if (app.currentView.type === "qa") {
      Panel.renderQaDetail(app.state, app.currentView.id, handlers, withBack());
    } else if (app.currentView.type === "examPoint") {
      Panel.renderExamPointDetail(app.state, app.currentView.id, handlers, withBack());
    } else if (app.currentView.type === "questionList") {
      Panel.renderQuestionList(app.state, handlers, app.currentView.filter, withBack());
    } else if (app.currentView.type === "examPointList") {
      Panel.renderExamPointList(app.state, handlers, app.currentView.filter, withBack());
    }
  }

  function renderReader() {
    if (!app.state) return;
    Reader.render(app.state, handlers, { annotationMode: app.annotationMode });
  }

  function updateWorkModeButtons() {
    document.querySelectorAll("[data-work-mode]").forEach(function (button) {
      var active = button.getAttribute("data-work-mode") === app.workMode;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", active ? "true" : "false");
    });
  }

  function setReaderModeFromContent() {
    if (app.workMode === "read") return;
    app.workMode = "read";
    updateWorkModeButtons();
  }

  function setWorkMode(mode) {
    app.workMode = mode || "read";
    app.annotationMode = "priority";
    updateWorkModeButtons();
    renderReader();
    showHome();
    if (app.workMode === "explain") refreshNewQuestionDrafts(false);
    if (app.workMode === "qa") refreshStudentQaDrafts(false);
  }

  function showHome() {
    if (!app.state) return;
    app.currentCardId = null;
    app.selectedEdgeTarget = null;
    app.currentView = { type: "home" };
    app.viewHistory = [];
    Panel.renderWorkbenchHome(app.state, handlers, app.workMode, app.workflowText[app.workMode] || "", app.visibleNotes, app.workflowState[app.workMode] || null);
  }

  function updateVisibleNotes(notes) {
    app.visibleNotes = notes || [];
    if (app.currentView && app.currentView.type === "home" && app.workMode === "read") {
      Panel.renderWorkbenchHome(app.state, handlers, app.workMode, app.workflowText.read || "", app.visibleNotes, app.workflowState[app.workMode] || null);
    }
  }

  function selectCard(cid, options) {
    if (!app.state || !cid) return;
    options = options || {};
    if (options && options.source === "reader") setReaderModeFromContent();
    if (!app.state.cardById[cid]) {
      setStatus("这条证据来自候选证据池，当前原文阅读区暂不能定位：" + cid, true);
      return;
    }
    navigateTo({ type: "card", id: cid }, { replace: options.replace });
    if (options && options.scroll) Reader.scrollToCard(app.state, cid);
  }

  function locateCard(cid) {
    if (!app.state || !cid) return;
    Reader.scrollToCard(app.state, cid);
  }

  function selectEdge(target) {
    app.selectedEdgeTarget = target || null;
    renderCurrentConcept();
  }

  function selectSection(sectionName, options) {
    if (!app.state || !sectionName) return;
    var cid = Store.getBestCardForSection(app.state, sectionName);
    if (!cid) {
      setStatus("该概念节点暂无可定位卡片：" + sectionName, true);
      return;
    }
    selectCard(cid, { scroll: !!(options && options.scroll), replace: options && options.replace });
  }

  function openGraphModal(cid) {
    if (!app.state || !cid) return;
    Panel.renderGraphModal(app.state, cid, handlers);
  }

  function selectQuestion(qid, options) {
    if (!app.state || !qid) return;
    navigateTo({ type: "question", id: qid }, options);
  }

  function selectQa(qaid, options) {
    if (!app.state || !qaid) return;
    navigateTo({ type: "qa", id: qaid }, options);
  }

  function selectExamPoint(epid, options) {
    if (!app.state || !epid) return;
    options = options || {};
    if (options && options.source === "reader") setReaderModeFromContent();
    navigateTo({ type: "examPoint", id: epid }, options);
  }

  function showQuestionList(filter) {
    if (!app.state) return;
    navigateTo({ type: "questionList", filter: filter || "all" });
  }

  function showExamPointList(filter) {
    if (!app.state) return;
    navigateTo({ type: "examPointList", filter: filter || "priority" });
  }

  function goBack() {
    var previous = null;
    while (app.viewHistory.length) {
      previous = app.viewHistory.pop();
      if (!isSameView(previous.view, app.currentView)) break;
      previous = null;
    }
    if (!previous) return;
    restoreSnapshot(previous);
  }

  function scrollToElement(id) {
    Reader.scrollToElement(id);
  }

  function scrollToParagraph(id) {
    Reader.scrollToParagraph(id);
  }

  function askRequired(message) {
    var value = window.prompt(message);
    if (value === null) return null;
    value = value.trim();
    return value || null;
  }

  function buildFeedbackEntry(epId, action) {
    var entry = {
      exam_point_id: epId,
      action: action,
      teacher_note: ""
    };
    if (action === "needs_rename") {
      entry.teacher_title = askRequired("请输入建议的新考点标题");
      if (!entry.teacher_title) return null;
    } else if (action === "needs_merge") {
      var target = askRequired("请输入要合并到的考点 ID 或考点标题");
      if (!target) return null;
      if (/^ep_/.test(target)) entry.merge_target_id = target;
      else entry.merge_target_title = target;
    } else if (action === "needs_split") {
      entry.split_notes = askRequired("请输入建议拆分成哪些考点");
      if (!entry.split_notes) return null;
    }
    if (action !== "confirmed") {
      entry.teacher_note = window.prompt("可补充原因或备注（可留空）", "") || "";
    }
    return entry;
  }

  function submitFeedback(epId, action) {
    var entry = buildFeedbackEntry(epId, action);
    if (!entry) return;
    FB.add(entry);
    renderCurrentView();
    updateFbBar();
  }

  function submitOptionFeedback(questionId, option, action, cardId, evidenceStatus) {
    var note = "";
    if (action !== "confirmed") {
      note = window.prompt("可补充原因或备注（可留空）", "") || "";
    }
    FB.add({
      feedback_type: "option_evidence",
      question_id: questionId,
      option: option,
      card_id: cardId || "",
      evidence_status: evidenceStatus || "",
      action: action,
      teacher_note: note
    });
    renderCurrentView();
    updateFbBar();
  }

  function runWorkflow(mode, text) {
    if (!mode) return;
    app.workMode = mode;
    app.workflowText[mode] = text || "";
    if (mode === "explain") {
      runNewQuestionAnalysis(text || "");
      return;
    }
    if (mode === "qa") {
      runStudentQaAnalysis(text || "");
      return;
    }
    updateWorkModeButtons();
    showHome();
  }

  function runStudentQaAnalysis(text) {
    var normalized = String(text || "").trim();
    var previous = app.workflowState.qa || {};
    app.workflowState.qa = {
      loading: !!normalized,
      error: normalized ? "" : "请先粘贴题目、选项和学生疑问。",
      draft: null,
      drafts: previous.drafts || [],
      draftsLoading: previous.draftsLoading || false,
      draftsError: previous.draftsError || "",
      historyLoadingId: "",
      historyCollapsed: !!previous.historyCollapsed,
      deletingDraftId: previous.deletingDraftId || "",
      evidenceExpanded: false,
      errorCode: ""
    };
    updateWorkModeButtons();
    showHome();
    if (!normalized) return;

    fetch(studentQaApiUrl("/analyze"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: normalized })
    }).then(function (res) {
      return res.json().then(function (payload) {
        if (!res.ok || !payload.ok) {
          throw buildApiError(res, payload);
        }
        return payload.draft;
      });
    }).then(function (draft) {
      var current = app.workflowState.qa || {};
      app.workflowState.qa = {
        loading: false,
        error: "",
        draft: draft,
        drafts: current.drafts || [],
        draftsLoading: current.draftsLoading || false,
        draftsError: current.draftsError || "",
        historyLoadingId: "",
        historyCollapsed: !!current.historyCollapsed,
        deletingDraftId: current.deletingDraftId || "",
        evidenceExpanded: false,
        errorCode: ""
      };
      showHome();
      refreshStudentQaDrafts(true);
    }).catch(function (err) {
      var current = app.workflowState.qa || {};
      app.workflowState.qa = {
        loading: false,
        error: "学生答疑服务不可用：" + (err && err.message ? err.message : err),
        errorCode: (err && err.code) || "",
        draft: null,
        drafts: current.drafts || [],
        draftsLoading: current.draftsLoading || false,
        draftsError: current.draftsError || "",
        historyLoadingId: "",
        historyCollapsed: !!current.historyCollapsed,
        deletingDraftId: current.deletingDraftId || "",
        evidenceExpanded: !!current.evidenceExpanded
      };
      showHome();
    });
  }

  function refreshStudentQaDrafts(force) {
    var state = app.workflowState.qa || {};
    if (!force && (state.draftsLoading || (state.drafts && state.drafts.length))) return;
    app.workflowState.qa = Object.assign({}, state, {
      draftsLoading: true,
      draftsError: ""
    });
    if (app.currentView && app.currentView.type === "home" && app.workMode === "qa") showHome();

    fetch(studentQaApiUrl("/drafts"))
      .then(function (res) {
        return res.json().then(function (payload) {
          if (!res.ok) throw new Error(payload.error || ("HTTP " + res.status));
          return payload.drafts || [];
        });
      })
      .then(function (drafts) {
        var current = app.workflowState.qa || {};
        app.workflowState.qa = Object.assign({}, current, {
          drafts: drafts,
          draftsLoading: false,
          draftsError: ""
        });
        if (app.currentView && app.currentView.type === "home" && app.workMode === "qa") showHome();
      })
      .catch(function (err) {
        var current = app.workflowState.qa || {};
        app.workflowState.qa = Object.assign({}, current, {
          draftsLoading: false,
          draftsError: "历史答疑读取失败：" + (err && err.message ? err.message : err)
        });
        if (app.currentView && app.currentView.type === "home" && app.workMode === "qa") showHome();
      });
  }

  function loadStudentQaDraft(draftId) {
    draftId = String(draftId || "").trim();
    if (!draftId) return;
    var state = app.workflowState.qa || {};
    app.workflowState.qa = Object.assign({}, state, {
      error: "",
      historyLoadingId: draftId
    });
    app.workMode = "qa";
    updateWorkModeButtons();
    showHome();

    fetch(studentQaApiUrl("/drafts/" + encodeURIComponent(draftId)))
      .then(function (res) {
        return res.json().then(function (payload) {
          if (!res.ok || !payload.ok) throw new Error(payload.error || ("HTTP " + res.status));
          return payload.draft;
        });
      })
      .then(function (draft) {
        var current = app.workflowState.qa || {};
        app.workflowText.qa = draft.raw_input || app.workflowText.qa || "";
        app.workflowState.qa = Object.assign({}, current, {
          loading: false,
          error: "",
          draft: draft,
          historyLoadingId: "",
          evidenceExpanded: false
        });
        showHome();
      })
      .catch(function (err) {
        var current = app.workflowState.qa || {};
        app.workflowState.qa = Object.assign({}, current, {
          historyLoadingId: "",
          error: "历史答疑读取失败：" + (err && err.message ? err.message : err)
        });
        showHome();
      });
  }

  function toggleStudentQaDraftHistory() {
    var state = app.workflowState.qa || {};
    app.workflowState.qa = Object.assign({}, state, {
      historyCollapsed: !state.historyCollapsed
    });
    showHome();
  }

  function toggleStudentQaEvidence() {
    var state = app.workflowState.qa || {};
    app.workflowState.qa = Object.assign({}, state, {
      evidenceExpanded: !state.evidenceExpanded
    });
    showHome();
  }

  function deleteStudentQaDraft(draftId) {
    draftId = String(draftId || "").trim();
    if (!draftId) return;
    if (!window.confirm("删除这条历史答疑？删除后不可恢复。")) return;
    var state = app.workflowState.qa || {};
    app.workflowState.qa = Object.assign({}, state, {
      deletingDraftId: draftId,
      draftsError: ""
    });
    showHome();

    fetch(studentQaApiUrl("/drafts/" + encodeURIComponent(draftId)), {
      method: "DELETE"
    }).then(function (res) {
      return res.json().then(function (payload) {
        if (!res.ok || !payload.ok) throw new Error(payload.error || ("HTTP " + res.status));
        return payload;
      });
    }).then(function () {
      var current = app.workflowState.qa || {};
      var currentDraft = current.draft || null;
      var deletingCurrent = currentDraft && currentDraft.draft_id === draftId;
      app.workflowState.qa = Object.assign({}, current, {
        draft: deletingCurrent ? null : currentDraft,
        drafts: (current.drafts || []).filter(function (draft) { return draft.draft_id !== draftId; }),
        deletingDraftId: "",
        historyLoadingId: "",
        draftsError: ""
      });
      if (deletingCurrent) app.workflowText.qa = "";
      showHome();
      refreshStudentQaDrafts(true);
    }).catch(function (err) {
      var current = app.workflowState.qa || {};
      app.workflowState.qa = Object.assign({}, current, {
        deletingDraftId: "",
        draftsError: "历史答疑删除失败：" + (err && err.message ? err.message : err)
      });
      showHome();
    });
  }

  function runNewQuestionAnalysis(text) {
    var normalized = String(text || "").trim();
    var previous = app.workflowState.explain || {};
    app.workflowState.explain = {
      loading: !!normalized,
      error: normalized ? "" : "请先粘贴题干和选项。",
      draft: null,
      drafts: previous.drafts || [],
      draftsLoading: previous.draftsLoading || false,
      draftsError: previous.draftsError || "",
      historyLoadingId: "",
      historyCollapsed: !!previous.historyCollapsed,
      deletingDraftId: previous.deletingDraftId || "",
      errorCode: ""
    };
    updateWorkModeButtons();
    showHome();
    if (!normalized) return;

    fetch(newQuestionApiUrl("/analyze"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: normalized })
    }).then(function (res) {
      return res.json().then(function (payload) {
        if (!res.ok || !payload.ok) {
          throw buildApiError(res, payload);
        }
        return payload.draft;
      });
    }).then(function (draft) {
      var current = app.workflowState.explain || {};
      app.workflowState.explain = {
        loading: false,
        error: "",
        draft: draft,
        drafts: current.drafts || [],
        draftsLoading: current.draftsLoading || false,
        draftsError: current.draftsError || "",
        historyLoadingId: "",
        historyCollapsed: !!current.historyCollapsed,
        deletingDraftId: current.deletingDraftId || "",
        errorCode: ""
      };
      showHome();
      refreshNewQuestionDrafts(true);
    }).catch(function (err) {
      var current = app.workflowState.explain || {};
      app.workflowState.explain = {
        loading: false,
        error: "新题解析服务不可用：" + (err && err.message ? err.message : err),
        errorCode: (err && err.code) || "",
        draft: null,
        drafts: current.drafts || [],
        draftsLoading: current.draftsLoading || false,
        draftsError: current.draftsError || "",
        historyLoadingId: "",
        historyCollapsed: !!current.historyCollapsed,
        deletingDraftId: current.deletingDraftId || ""
      };
      showHome();
    });
  }

  function refreshNewQuestionDrafts(force) {
    var state = app.workflowState.explain || {};
    if (!force && (state.draftsLoading || (state.drafts && state.drafts.length))) return;
    app.workflowState.explain = Object.assign({}, state, {
      draftsLoading: true,
      draftsError: ""
    });
    if (app.currentView && app.currentView.type === "home" && app.workMode === "explain") showHome();

    fetch(newQuestionApiUrl("/drafts"))
      .then(function (res) {
        return res.json().then(function (payload) {
          if (!res.ok) throw new Error(payload.error || ("HTTP " + res.status));
          return payload.drafts || [];
        });
      })
      .then(function (drafts) {
        var current = app.workflowState.explain || {};
        app.workflowState.explain = Object.assign({}, current, {
          drafts: drafts,
          draftsLoading: false,
          draftsError: ""
        });
        if (app.currentView && app.currentView.type === "home" && app.workMode === "explain") showHome();
      })
      .catch(function (err) {
        var current = app.workflowState.explain || {};
        app.workflowState.explain = Object.assign({}, current, {
          draftsLoading: false,
          draftsError: "历史草稿读取失败：" + (err && err.message ? err.message : err)
        });
        if (app.currentView && app.currentView.type === "home" && app.workMode === "explain") showHome();
      });
  }

  function loadNewQuestionDraft(draftId) {
    draftId = String(draftId || "").trim();
    if (!draftId) return;
    var state = app.workflowState.explain || {};
    app.workflowState.explain = Object.assign({}, state, {
      error: "",
      historyLoadingId: draftId
    });
    app.workMode = "explain";
    updateWorkModeButtons();
    showHome();

    fetch(newQuestionApiUrl("/drafts/" + encodeURIComponent(draftId)))
      .then(function (res) {
        return res.json().then(function (payload) {
          if (!res.ok || !payload.ok) throw new Error(payload.error || ("HTTP " + res.status));
          return payload.draft;
        });
      })
      .then(function (draft) {
        var current = app.workflowState.explain || {};
        app.workflowText.explain = draft.sanitized_input || draft.raw_input || app.workflowText.explain || "";
        app.workflowState.explain = Object.assign({}, current, {
          loading: false,
          error: "",
          draft: draft,
          historyLoadingId: ""
        });
        showHome();
      })
      .catch(function (err) {
        var current = app.workflowState.explain || {};
        app.workflowState.explain = Object.assign({}, current, {
          historyLoadingId: "",
          error: "历史草稿读取失败：" + (err && err.message ? err.message : err)
        });
        showHome();
      });
  }

  function toggleNewQuestionDraftHistory() {
    var state = app.workflowState.explain || {};
    app.workflowState.explain = Object.assign({}, state, {
      historyCollapsed: !state.historyCollapsed
    });
    showHome();
  }

  function deleteNewQuestionDraft(draftId) {
    draftId = String(draftId || "").trim();
    if (!draftId) return;
    if (!window.confirm("删除这条历史草稿？删除后不可恢复。")) return;
    var state = app.workflowState.explain || {};
    app.workflowState.explain = Object.assign({}, state, {
      deletingDraftId: draftId,
      draftsError: ""
    });
    showHome();

    fetch(newQuestionApiUrl("/drafts/" + encodeURIComponent(draftId)), {
      method: "DELETE"
    }).then(function (res) {
      return res.json().then(function (payload) {
        if (!res.ok || !payload.ok) throw new Error(payload.error || ("HTTP " + res.status));
        return payload;
      });
    }).then(function () {
      var current = app.workflowState.explain || {};
      var currentDraft = current.draft || null;
      var deletingCurrent = currentDraft && currentDraft.draft_id === draftId;
      app.workflowState.explain = Object.assign({}, current, {
        draft: deletingCurrent ? null : currentDraft,
        drafts: (current.drafts || []).filter(function (draft) { return draft.draft_id !== draftId; }),
        deletingDraftId: "",
        historyLoadingId: "",
        draftsError: ""
      });
      if (deletingCurrent) app.workflowText.explain = "";
      showHome();
      refreshNewQuestionDrafts(true);
    }).catch(function (err) {
      var current = app.workflowState.explain || {};
      app.workflowState.explain = Object.assign({}, current, {
        deletingDraftId: "",
        draftsError: "历史草稿删除失败：" + (err && err.message ? err.message : err)
      });
      showHome();
    });
  }

  function newQuestionApiUrl(path) {
    var suffix = String(path || "");
    if (suffix.charAt(0) !== "/") suffix = "/" + suffix;
    var host = window.location.hostname || "";
    var isLocal = host === "127.0.0.1" || host === "localhost" || host === "";
    if (isLocal) return "http://127.0.0.1:8765/api/new-question" + suffix;
    return "/cams-api/new-question" + suffix;
  }

  function studentQaApiUrl(path) {
    var suffix = String(path || "");
    if (suffix.charAt(0) !== "/") suffix = "/" + suffix;
    var host = window.location.hostname || "";
    var isLocal = host === "127.0.0.1" || host === "localhost" || host === "";
    if (isLocal) return "http://127.0.0.1:8766/api/student-qa" + suffix;
    return "/cams-api/student-qa" + suffix;
  }

  function updateFbBar() {
    var bar = U.byId("feedbackBar");
    if (!bar) return;
    var cnt = FB.count();
    bar.style.display = "flex";
    bar.innerHTML = '<span class="fb-count">反馈 ' + cnt + " 条</span>" +
      '<span><button class="fb-export" type="button">导出 JSON</button>' +
      '<button class="fb-clear" type="button">清空</button></span>';
    bar.querySelector(".fb-export").addEventListener("click", function () { FB.exportJSON(); });
    bar.querySelector(".fb-clear").addEventListener("click", function () { FB.clear(); updateFbBar(); renderCurrentView(); });
  }

  var handlers = {
    locateCard: locateCard,
    openGraphModal: openGraphModal,
    scrollToElement: scrollToElement,
    scrollToParagraph: scrollToParagraph,
    updateVisibleNotes: updateVisibleNotes,
    selectCard: selectCard,
    selectEdge: selectEdge,
    selectExamPoint: selectExamPoint,
    selectQa: selectQa,
    selectQuestion: selectQuestion,
    selectSection: selectSection,
    showHome: showHome,
    showExamPointList: showExamPointList,
    showQuestionList: showQuestionList,
    runWorkflow: runWorkflow,
    refreshNewQuestionDrafts: function () { refreshNewQuestionDrafts(true); },
    loadNewQuestionDraft: loadNewQuestionDraft,
    toggleNewQuestionDraftHistory: toggleNewQuestionDraftHistory,
    deleteNewQuestionDraft: deleteNewQuestionDraft,
    refreshStudentQaDrafts: function () { refreshStudentQaDrafts(true); },
    loadStudentQaDraft: loadStudentQaDraft,
    toggleStudentQaDraftHistory: toggleStudentQaDraftHistory,
    toggleStudentQaEvidence: toggleStudentQaEvidence,
    deleteStudentQaDraft: deleteStudentQaDraft,
    setWorkMode: setWorkMode,
    goBack: goBack,
    submitFeedback: submitFeedback,
    submitOptionFeedback: submitOptionFeedback
  };

  function bindChrome() {
    document.addEventListener("click", function (event) {
      var backButton = event.target && event.target.closest ? event.target.closest("[data-panel-back]") : null;
      if (!backButton) return;
      event.preventDefault();
      event.stopPropagation();
      goBack();
    }, true);

    document.querySelectorAll("[data-work-mode]").forEach(function (button) {
      button.addEventListener("click", function () {
        setWorkMode(button.getAttribute("data-work-mode"));
      });
    });

    var tocPane = document.querySelector(".toc-pane");
    var tocToggle = U.byId("tocToggleButton");
    var storageKey = "cams.tocCollapsed";

    function rememberTocState(collapsed) {
      try {
        window.localStorage.setItem(storageKey, collapsed ? "1" : "0");
      } catch (error) {
        // The layout still works when localStorage is unavailable.
      }
    }

    function setTocCollapsed(collapsed, shouldRemember) {
      if (!tocPane || !tocToggle) return;
      tocPane.classList.toggle("collapsed", collapsed);
      tocToggle.textContent = collapsed ? "›" : "‹";
      tocToggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
      tocToggle.setAttribute("aria-label", collapsed ? "展开目录" : "收起目录");
      tocToggle.setAttribute("title", collapsed ? "展开目录" : "收起目录");
      if (shouldRemember) rememberTocState(collapsed);
    }

    if (tocPane && tocToggle) {
      var savedCollapsed = false;
      try {
        savedCollapsed = window.localStorage.getItem(storageKey) === "1";
      } catch (error) {
        savedCollapsed = false;
      }
      setTocCollapsed(savedCollapsed, false);

      tocToggle.addEventListener("click", function (event) {
        event.stopPropagation();
        setTocCollapsed(!tocPane.classList.contains("collapsed"), true);
      });

      tocPane.addEventListener("click", function () {
        if (tocPane.classList.contains("collapsed")) setTocCollapsed(false, true);
      });
    }
  }

  function init() {
    bindChrome();
    Store.load().then(function (state) {
      app.state = state;
      updateWorkModeButtons();
      renderReader();
      Search.bind(state, handlers);
      updateFbBar();
      showHome();
    }).catch(function (error) {
      setStatus(error.message, true);
      var pane = U.byId("detailContent") || U.byId("detailPane");
      if (pane) {
        pane.innerHTML = '<div class="empty-panel"><h2 class="error">加载失败</h2><p>' + U.escapeHtml(error.message) + "</p></div>";
      }
    });
  }

  window.CamsApp = {
    init: init,
    goBack: goBack,
    locateCard: locateCard,
    selectCard: selectCard,
    selectExamPoint: selectExamPoint,
    selectQuestion: selectQuestion,
    selectSection: selectSection,
    showHome: showHome,
    setWorkMode: setWorkMode,
    showExamPointList: showExamPointList
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
