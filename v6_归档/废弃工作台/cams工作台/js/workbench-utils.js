(function () {
  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function escapeRegExp(value) {
    return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function normalizeText(value) {
    return String(value == null ? "" : value).toLowerCase().trim();
  }

  function shortText(value, max) {
    var text = String(value == null ? "" : value).replace(/\s+/g, " ").trim();
    if (text.length <= max) return text;
    return text.slice(0, Math.max(0, max - 1)) + "…";
  }

  function unique(values) {
    var seen = {};
    var out = [];
    (values || []).forEach(function (value) {
      if (!value || seen[value]) return;
      seen[value] = true;
      out.push(value);
    });
    return out;
  }

  function byId(id) {
    return document.getElementById(id);
  }

  function setHidden(el, hidden) {
    if (!el) return;
    if (hidden) el.setAttribute("hidden", "");
    else el.removeAttribute("hidden");
  }

  function scoreText(text, query) {
    var body = normalizeText(text);
    var q = normalizeText(query);
    if (!q || !body) return 0;
    if (body === q) return 100;
    if (body.indexOf(q) >= 0) return 50 + Math.min(25, q.length);
    var words = q.split(/\s+/).filter(Boolean);
    var hits = words.filter(function (word) { return body.indexOf(word) >= 0; }).length;
    return hits ? hits * 8 : 0;
  }

  function makeSnippet(text, query, max) {
    var source = String(text == null ? "" : text).replace(/\s+/g, " ").trim();
    var q = normalizeText(query);
    var lower = source.toLowerCase();
    var index = q ? lower.indexOf(q) : -1;
    if (index < 0) return escapeHtml(shortText(source, max));
    var start = Math.max(0, index - 28);
    var end = Math.min(source.length, index + q.length + 44);
    var snippet = (start > 0 ? "..." : "") + source.slice(start, end) + (end < source.length ? "..." : "");
    var safe = escapeHtml(snippet);
    return safe.replace(new RegExp(escapeRegExp(escapeHtml(source.slice(index, index + q.length))), "i"), function (m) {
      return "<mark>" + m + "</mark>";
    });
  }

  window.CamsUtils = {
    byId: byId,
    escapeHtml: escapeHtml,
    escapeRegExp: escapeRegExp,
    makeSnippet: makeSnippet,
    normalizeText: normalizeText,
    scoreText: scoreText,
    setHidden: setHidden,
    shortText: shortText,
    unique: unique
  };
})();
