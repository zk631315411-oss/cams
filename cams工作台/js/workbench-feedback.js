(function () {
  var FB_KEY = "cams.exam_point_feedback";

  function load() {
    try { return JSON.parse(window.localStorage.getItem(FB_KEY) || "[]"); } catch (e) { return []; }
  }

  function save(list) {
    window.localStorage.setItem(FB_KEY, JSON.stringify(list));
  }

  function normalizeEntry(input, action, note) {
    var entry = typeof input === "object" ? input : {
      exam_point_id: input,
      action: action,
      teacher_note: note || ""
    };
    var row = {
      exam_point_id: entry.exam_point_id || "",
      feedback_type: entry.feedback_type || "exam_point",
      action: entry.action || "",
      created_at: entry.created_at || new Date().toISOString(),
      teacher_note: entry.teacher_note || ""
    };
    [
      "question_id",
      "option",
      "card_id",
      "evidence_status",
      "teacher_title",
      "merge_target_id",
      "merge_target_title",
      "split_notes",
      "source_card_ids",
      "question_ids",
      "qa_ids"
    ].forEach(function (key) {
      if (entry[key] !== undefined && entry[key] !== "") row[key] = entry[key];
    });
    return row;
  }

  function add(entry, action, note) {
    var list = load();
    list.push(normalizeEntry(entry, action, note));
    save(list);
    return list;
  }

  function count() {
    return load().length;
  }

  function clear() {
    save([]);
  }

  function exportJSON() {
    var list = load();
    var payload = {
      version: "0.1",
      exported_at: new Date().toISOString(),
      source: "cams-workbench-local",
      feedback: list
    };
    var blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "cams_exam_point_feedback_" + new Date().toISOString().slice(0, 10) + ".json";
    a.click();
    return list.length;
  }

  window.CamsFeedback = {
    load: load,
    add: add,
    count: count,
    clear: clear,
    exportJSON: exportJSON
  };
})();
