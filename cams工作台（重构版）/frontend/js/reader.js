(function () {
  var U = window.CamsUtils;
  var currentLanguage = "zh";
  var currentPage = 1;
  var currentZoom = 1;
  var currentState = null;
  var currentHandlers = null;
  var loadedStart = 1;
  var loadedEnd = 1;
  var isExtending = false;

  function pageCount() { return (currentState && currentState.textbookRelease.counts.bilingual_pdf_pages) || 1; }
  function clampPage(value) { return Math.max(1, Math.min(pageCount(), Number(value) || 1)); }
  function pageUrl(language, page) { return "api/textbook-page?lang=" + language + "&page=" + page + "&scale=1.8"; }
  function chapterLabel(chapter) {
    var en = chapter.title_en || chapter.title;
    var zh = chapter.title_zh || en;
    if (currentLanguage === "en") return { primary: en, secondary: zh };
    return { primary: zh, secondary: en };
  }
  function renderToc() {
    var toc = U.byId("tocList");
    if (!toc || !currentState || !currentHandlers) return;
    toc.innerHTML = "";
    currentState.chapters.forEach(function (chapter) {
      var label = chapterLabel(chapter);
      var button = document.createElement("button");
      button.type = "button";
      button.className = "toc-item";
      button.innerHTML = "<span class=\"toc-item-primary\">" + U.escapeHtml(label.primary) + "</span><span class=\"toc-item-secondary\">" + U.escapeHtml(label.secondary) + "</span><small>" + chapter.unit_ids.length + "</small>";
      button.addEventListener("click", function () { currentHandlers.selectChapter(chapter.chapter_id); });
      toc.appendChild(button);
    });
  }
  function pageMarkup(page) {
    var content = currentLanguage === "both"
      ? "<div class=\"pdf-page-spread\" style=\"--page-zoom:" + currentZoom + "\"><div class=\"pdf-page-frame\"><img class=\"textbook-page\" alt=\"中文教材第 " + page + " 页\" src=\"" + pageUrl("zh", page) + "\"></div><div class=\"pdf-page-frame\"><img class=\"textbook-page\" alt=\"英文教材第 " + page + " 页\" src=\"" + pageUrl("en", page) + "\"></div></div>"
      : "<div class=\"pdf-page-frame\" style=\"--page-zoom:" + currentZoom + "\"><img class=\"textbook-page\" alt=\"" + (currentLanguage === "en" ? "英文" : "中文") + "教材第 " + page + " 页\" src=\"" + pageUrl(currentLanguage, page) + "\"></div>";
    return "<article class=\"pdf-page\" data-page=\"" + page + "\"><span class=\"pdf-page-label\">PDF 第 " + page + " 页</span>" + content + "</article>";
  }
  function updateToolbar() { var reader = U.byId("reader"); if (!reader) return; var input = reader.querySelector(".pdf-page-input input"); if (input) input.value = currentPage; var label = reader.querySelector(".pdf-zoom-label"); if (label) label.textContent = Math.round(currentZoom * 100) + "%"; }
  function appendRange(start, end, prepend) { var scroll = U.byId("pdfScroll"); if (!scroll || start > end) return; var html = ""; for (var page = start; page <= end; page += 1) html += pageMarkup(page); if (prepend) { var before = scroll.scrollHeight; scroll.insertAdjacentHTML("afterbegin", html); scroll.scrollTop += scroll.scrollHeight - before; } else { scroll.insertAdjacentHTML("beforeend", html); } }
  function updateCurrentPageFromScroll() { var scroll = U.byId("pdfScroll"); if (!scroll) return; var scrollTop = scroll.getBoundingClientRect().top; var bestPage = currentPage; var bestDistance = Infinity; scroll.querySelectorAll(".pdf-page").forEach(function (element) { var distance = Math.abs(element.getBoundingClientRect().top - scrollTop - 12); if (distance < bestDistance) { bestDistance = distance; bestPage = Number(element.dataset.page); } }); if (bestPage !== currentPage) { currentPage = bestPage; updateToolbar(); } }
  function extendOnScroll() { var scroll = U.byId("pdfScroll"); if (!scroll || isExtending) return; isExtending = true; var threshold = 500; if (scroll.scrollTop + scroll.clientHeight > scroll.scrollHeight - threshold && loadedEnd < pageCount()) { var nextEnd = Math.min(pageCount(), loadedEnd + 3); appendRange(loadedEnd + 1, nextEnd, false); loadedEnd = nextEnd; } if (scroll.scrollTop < threshold && loadedStart > 1) { var nextStart = Math.max(1, loadedStart - 3); appendRange(nextStart, loadedStart - 1, true); loadedStart = nextStart; } updateCurrentPageFromScroll(); isExtending = false; }
  function renderWindow(focusPage) { var reader = U.byId("reader"); if (!reader || !currentState) return; reader.classList.add("pdf-reader"); currentPage = clampPage(focusPage); loadedStart = currentPage; loadedEnd = Math.min(pageCount(), currentPage + 2); reader.innerHTML = "<div class=\"pdf-toolbar\"><label class=\"pdf-page-input\">当前位置 <input type=\"number\" min=\"1\" max=\"" + pageCount() + "\" value=\"" + currentPage + "\" aria-label=\"跳转页码\"> / " + pageCount() + " 页</label><span class=\"pdf-toolbar-spacer\"></span><button class=\"pdf-control\" type=\"button\" data-pdf-action=\"zoom-out\" aria-label=\"缩小\" title=\"缩小\">-</button><span class=\"pdf-zoom-label\">" + Math.round(currentZoom * 100) + "%</span><button class=\"pdf-control\" type=\"button\" data-pdf-action=\"zoom-in\" aria-label=\"放大\" title=\"放大\">+</button></div><div class=\"pdf-scroll\" id=\"pdfScroll\"></div>"; appendRange(loadedStart, loadedEnd, false); var scroll = U.byId("pdfScroll"); scroll.addEventListener("scroll", extendOnScroll, { passive: true }); var input = reader.querySelector(".pdf-page-input input"); input.addEventListener("change", function () { renderWindow(clampPage(input.value)); }); reader.querySelectorAll("[data-pdf-action]").forEach(function (button) { button.addEventListener("click", function () { currentZoom = button.dataset.pdfAction === "zoom-in" ? Math.min(1.8, Number((currentZoom + 0.2).toFixed(1))) : Math.max(0.8, Number((currentZoom - 0.2).toFixed(1))); renderWindow(currentPage); }); }); }
  function render(state, handlers) { currentState = state; currentHandlers = handlers; renderToc(); var first = state.units[0]; renderWindow(first && first.pdf_page ? first.pdf_page : 1); }
  function locateUnit(unit) { if (unit) renderWindow(unit.pdf_page); }
  function setLanguage(language) { currentLanguage = language; renderToc(); renderWindow(currentPage); }
  window.CamsReader = { render: render, locateUnit: locateUnit, setLanguage: setLanguage };
})();
