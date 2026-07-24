(function () {
  var storageKey = "cams-v7-workbench-layout-v1";
  var minReaderWidth = 500;
  var minPdfHeight = 260;
  var minBottomHeight = 64;
  var minWidths = { toc: 180, detail: 280 };
  var defaults = { toc: 250, detail: 420, bottom: 144 };
  var activePane = null;
  var activeReaderResize = null;
  var readerHandlesBound = false;

  function isDesktop() { return window.innerWidth > 1000; }
  function getWidth(name) {
    var element = document.querySelector(name === "toc" ? ".toc-pane" : ".detail-pane");
    return element ? Math.round(element.getBoundingClientRect().width) : defaults[name];
  }
  function getLayout() {
    try {
      var saved = JSON.parse(window.localStorage.getItem(storageKey) || "{}");
      return { toc: Number(saved.toc) || defaults.toc, detail: Number(saved.detail) || defaults.detail, bottom: Number(saved.bottom) || defaults.bottom };
    } catch (error) {
      return { toc: defaults.toc, detail: defaults.detail, bottom: defaults.bottom };
    }
  }
  function saveLayout(layout) {
    try { window.localStorage.setItem(storageKey, JSON.stringify(Object.assign(getLayout(), layout))); } catch (error) {}
  }
  function maxWidth(name, layout) {
    var other = name === "toc" ? layout.detail : layout.toc;
    return Math.max(minWidths[name], window.innerWidth - other - minReaderWidth - 24);
  }
  function clamp(value, name, layout) {
    return Math.round(Math.max(minWidths[name], Math.min(maxWidth(name, layout), value)));
  }
  function applyLayout(layout, persist) {
    if (!isDesktop()) return;
    var next = {
      toc: clamp(layout.toc, "toc", layout),
      detail: clamp(layout.detail, "detail", layout)
    };
    next.toc = clamp(next.toc, "toc", next);
    next.detail = clamp(next.detail, "detail", next);
    document.documentElement.style.setProperty("--toc-width", next.toc + "px");
    document.documentElement.style.setProperty("--panel-width", next.detail + "px");
    document.querySelectorAll("[data-resize-pane]").forEach(function (handle) {
      var pane = handle.dataset.resizePane;
      handle.setAttribute("aria-valuemin", minWidths[pane]);
      handle.setAttribute("aria-valuemax", maxWidth(pane, next));
      handle.setAttribute("aria-valuenow", next[pane]);
    });
    if (persist) saveLayout(next);
  }
  function resize(pane, clientX, persist) {
    var layout = { toc: getWidth("toc"), detail: getWidth("detail") };
    var desired = pane === "toc" ? clientX : window.innerWidth - clientX;
    layout[pane] = clamp(desired, pane, layout);
    applyLayout(layout, persist);
  }
  function maxBottomHeight() {
    var readerPane = document.querySelector(".reader-pane");
    var topbar = document.querySelector(".topbar");
    return Math.max(minBottomHeight, (readerPane ? readerPane.clientHeight : 0) - (topbar ? topbar.offsetHeight : 0) - minPdfHeight - 12);
  }
  function getBottomHeight() {
    var pane = document.querySelector(".reader-bottom-pane");
    return pane ? Math.round(pane.getBoundingClientRect().height) : defaults.bottom;
  }
  function applyReaderHeight(value, persist) {
    if (!isDesktop()) return;
    var next = Math.round(Math.max(minBottomHeight, Math.min(maxBottomHeight(), value)));
    document.documentElement.style.setProperty("--reader-bottom-height", next + "px");
    document.querySelectorAll("[data-resize-reader-height]").forEach(function (handle) {
      handle.setAttribute("aria-valuemin", minBottomHeight);
      handle.setAttribute("aria-valuemax", maxBottomHeight());
      handle.setAttribute("aria-valuenow", next);
    });
    if (persist) saveLayout({ bottom: next });
  }
  function bindReaderHandle(handle) {
    if (!handle || handle.dataset.readerResizeBound === "1") return;
    handle.dataset.readerResizeBound = "1";
    handle.addEventListener("pointerdown", beginReaderResize);
    handle.addEventListener("pointermove", moveReaderResize);
    handle.addEventListener("pointerup", endReaderResize);
    handle.addEventListener("pointercancel", endReaderResize);
    handle.addEventListener("keydown", nudgeReader);
    handle.addEventListener("dblclick", resetReader);
  }
  function beginResize(event) {
    if (!isDesktop()) return;
    activePane = event.currentTarget.dataset.resizePane;
    document.body.classList.add("is-resizing");
    event.currentTarget.setPointerCapture(event.pointerId);
    resize(activePane, event.clientX, false);
    event.preventDefault();
  }
  function moveResize(event) {
    if (!activePane) return;
    resize(activePane, event.clientX, false);
  }
  function endResize() {
    if (!activePane) return;
    var layout = { toc: getWidth("toc"), detail: getWidth("detail") };
    applyLayout(layout, true);
    activePane = null;
    document.body.classList.remove("is-resizing");
  }
  function resizeReader(clientY, persist) {
    var readerPane = document.querySelector(".reader-pane");
    if (!readerPane) return;
    applyReaderHeight(readerPane.getBoundingClientRect().bottom - clientY, persist);
  }
  function beginReaderResize(event) {
    if (!isDesktop()) return;
    activeReaderResize = event.pointerId;
    document.body.classList.add("is-resizing-vertical");
    event.currentTarget.setPointerCapture(event.pointerId);
    resizeReader(event.clientY, false);
    event.preventDefault();
  }
  function moveReaderResize(event) {
    if (activeReaderResize !== event.pointerId) return;
    resizeReader(event.clientY, false);
  }
  function endReaderResize() {
    if (activeReaderResize == null) return;
    applyReaderHeight(getBottomHeight(), true);
    activeReaderResize = null;
    document.body.classList.remove("is-resizing-vertical");
  }
  function nudge(event) {
    var pane = event.currentTarget.dataset.resizePane;
    if (!isDesktop() || (event.key !== "ArrowLeft" && event.key !== "ArrowRight")) return;
    var layout = { toc: getWidth("toc"), detail: getWidth("detail") };
    var direction = event.key === "ArrowRight" ? 1 : -1;
    layout[pane] += pane === "toc" ? direction * 16 : direction * -16;
    applyLayout(layout, true);
    event.preventDefault();
  }
  function resetPane(event) {
    var pane = event.currentTarget.dataset.resizePane;
    var layout = { toc: getWidth("toc"), detail: getWidth("detail") };
    layout[pane] = defaults[pane];
    applyLayout(layout, true);
  }
  function nudgeReader(event) {
    if (!isDesktop() || (event.key !== "ArrowUp" && event.key !== "ArrowDown")) return;
    applyReaderHeight(getBottomHeight() + (event.key === "ArrowUp" ? 16 : -16), true);
    event.preventDefault();
  }
  function resetReader() { applyReaderHeight(defaults.bottom, true); }
  function init() {
    applyLayout(getLayout(), false);
    applyReaderHeight(getLayout().bottom, false);
    document.querySelectorAll("[data-resize-pane]").forEach(function (handle) {
      handle.addEventListener("pointerdown", beginResize);
      handle.addEventListener("pointermove", moveResize);
      handle.addEventListener("pointerup", endResize);
      handle.addEventListener("pointercancel", endResize);
      handle.addEventListener("keydown", nudge);
      handle.addEventListener("dblclick", resetPane);
    });
    bindReaderHandles();
    window.addEventListener("resize", function () {
      applyLayout({ toc: getWidth("toc"), detail: getWidth("detail") }, false);
      applyReaderHeight(getBottomHeight(), false);
    });
  }
  function bindReaderHandles() {
    document.querySelectorAll("[data-resize-reader-height]").forEach(bindReaderHandle);
    readerHandlesBound = true;
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
  window.CamsLayout = {
    refreshReaderHandles: bindReaderHandles
  };
})();
