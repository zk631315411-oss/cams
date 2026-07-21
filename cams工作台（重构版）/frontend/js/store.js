(function () {
  var BASE = "data/releases/v7/";

  function getJson(path) {
    return fetch(path).then(function (response) {
      if (!response.ok) {
        var error = new Error(path + " 加载失败: " + response.status);
        error.status = response.status;
        throw error;
      }
      return response.json();
    });
  }
  function values(document) { return (document && document.items) || []; }
  function releasePath(active) {
    if (!active || !active.release_path) throw new Error("活动发布指针缺少 release_path。");
    return BASE + active.release_path.replace(/\/$/, "") + "/";
  }
  function loadTextbook() {
    return getJson(BASE + "textbook-active.json").then(function (active) {
      var root = releasePath(active);
      return Promise.all([Promise.resolve(active), getJson(root + "manifest.json"), getJson(root + "units.json"), getJson(root + "chapters.json"), getJson(root + "page-map.json")]);
    }).then(function (items) {
      var manifest = items[1];
      if (manifest.schema_version !== "cams-v7-textbook-release/v1" || !manifest.validation || !manifest.validation.valid) throw new Error("活动教材包未通过 v7 教材发布校验。");
      return { active: items[0], manifest: manifest, units: values(items[2]), chapters: values(items[3]), pageMap: items[4], root: releasePath(items[0]) };
    });
  }
  function loadEvidence(textbook) {
    return getJson(BASE + "active.json").then(function (active) {
      var root = releasePath(active);
      return Promise.all([Promise.resolve(active), getJson(root + "manifest.json"), getJson(root + "questions.json"), getJson(root + "evidence.json")]);
    }).then(function (items) {
      var manifest = items[1];
      if (manifest.schema_version !== "cams-v7-workbench-release/v1" || !manifest.validation || !manifest.validation.valid) throw new Error("题目证据发布包未通过校验。");
      if (!manifest.source || !manifest.source.units || manifest.source.units.sha256 !== textbook.manifest.source.units.sha256) throw new Error("题目证据包与当前教材冻结版本不一致，已拒绝叠加。");
      return { active: items[0], manifest: manifest, questions: values(items[2]), evidence: values(items[3]) };
    }).catch(function (error) {
      if (error.status === 404) return null;
      return { error: error };
    });
  }
  function buildState(textbook, evidenceRelease) {
    var state = {
      textbookRelease: textbook.manifest,
      evidenceRelease: evidenceRelease && !evidenceRelease.error ? evidenceRelease.manifest : null,
      evidenceLoadError: evidenceRelease && evidenceRelease.error ? evidenceRelease.error.message : "",
      textbook: { zhPdf: textbook.root + textbook.manifest.assets.zh_pdf, enPdf: textbook.root + textbook.manifest.assets.en_pdf, pageMap: textbook.pageMap },
      units: textbook.units,
      chapters: textbook.chapters,
      questions: evidenceRelease && !evidenceRelease.error ? evidenceRelease.questions : [],
      evidence: evidenceRelease && !evidenceRelease.error ? evidenceRelease.evidence : [],
      unitById: {}, questionById: {}, evidenceByQuestionId: {}, questionsByUnitId: {}
    };
    state.units.forEach(function (unit) { state.unitById[unit.unit_id] = unit; });
    state.questions.forEach(function (question) { state.questionById[question.question_id] = question; });
    state.evidence.forEach(function (entry) {
      state.evidenceByQuestionId[entry.question_id] = entry;
      (entry.option_analysis || []).forEach(function (option) {
        (option.evidence_cards || []).forEach(function (card) {
          var list = state.questionsByUnitId[card.unit_id] || (state.questionsByUnitId[card.unit_id] = []);
          if (list.indexOf(entry.question_id) < 0) list.push(entry.question_id);
        });
      });
    });
    return state;
  }
  function load() {
    return loadTextbook().then(function (textbook) { return loadEvidence(textbook).then(function (evidence) { return buildState(textbook, evidence); }); }).catch(function (error) {
      if (/textbook-active\.json/.test(error.message || "")) throw new Error("当前没有已激活的 v7 教材包。请先使用 tools/v7_release/build_textbook_release.py 发布双语教材。");
      throw error;
    });
  }
  window.CamsStore = {
    load: load,
    getUnit: function (state, id) { return state.unitById[id] || null; },
    getQuestion: function (state, id) { return state.questionById[id] || null; },
    getEvidence: function (state, id) { return state.evidenceByQuestionId[id] || null; },
    getQuestionsForUnit: function (state, id) { return (state.questionsByUnitId[id] || []).map(function (questionId) { return state.questionById[questionId]; }).filter(Boolean); }
  };
})();
