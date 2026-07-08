(function () {
  var U = window.CamsUtils;
  var Store = window.CamsStore;

  function makeSubId(sectionId, index) {
    return "sub-" + sectionId.replace(/[^a-zA-Z0-9_-]/g, "-") + "-" + index;
  }

  function compactText(value) {
    var text = String(value == null ? "" : value);
    var compact = "";
    var map = [];
    for (var i = 0; i < text.length; i += 1) {
      if (/\s/.test(text.charAt(i))) continue;
      compact += text.charAt(i);
      map.push(i);
    }
    return { text: compact, map: map };
  }

  function findTextRange(text, quote) {
    var source = String(text || "");
    var needle = String(quote || "").trim();
    if (needle.length < 8) return null;

    var start = source.indexOf(needle);
    if (start >= 0) return { start: start, end: Math.min(source.length, start + needle.length) };

    if (needle.length > 22) {
      var prefix = needle.slice(0, Math.min(40, needle.length));
      start = source.indexOf(prefix);
      if (start >= 0) return { start: start, end: Math.min(source.length, start + needle.length) };
    }

    var compactSource = compactText(source);
    var compactNeedle = compactText(needle).text;
    if (compactNeedle.length < 8) return null;
    var compactStart = compactSource.text.indexOf(compactNeedle);
    if (compactStart < 0) return null;
    var compactEnd = compactStart + compactNeedle.length - 1;
    return {
      start: compactSource.map[compactStart],
      end: Math.min(source.length, compactSource.map[compactEnd] + 1)
    };
  }

  function pushRange(ranges, seen, range) {
    if (!range || range.start < 0 || range.end <= range.start) return;
    var key = [range.start, range.end, range.cardId || "", range.examPointId || ""].join("|");
    if (seen[key]) return;
    seen[key] = true;
    ranges.push(range);
  }

  function cleanHighlightRanges(ranges) {
    var clean = [];
    var occupiedEnd = -1;
    ranges.forEach(function (range) {
      if (range.start < occupiedEnd) return;
      clean.push(range);
      occupiedEnd = range.end;
    });
    return clean;
  }

  function cleanHighlightItems(items) {
    var clean = [];
    var occupiedEnd = -1;
    items.forEach(function (item) {
      if (item.range.start < occupiedEnd) return;
      clean.push(item);
      occupiedEnd = item.range.end;
    });
    return clean;
  }

  function findHighlightRanges(paragraph, state, options) {
    var text = paragraph.text || "";
    var ranges = [];
    var seen = {};

    U.unique((paragraph.highlightCardIds || []).concat(paragraph.cardIds || [])).forEach(function (cid) {
      if (!Store.getExamPointsForCard(state, cid).length) return;
      var card = state.cardById[cid];
      var citation = card && card.citation ? card.citation.trim() : "";
      var match = findTextRange(text, citation);
      if (!match) return;
      pushRange(ranges, seen, { start: match.start, end: match.end, cardId: cid, citation: text.slice(match.start, match.end) });
    });

    (state.examPoints || []).forEach(function (ep) {
      (ep.source_card_details || []).forEach(function (detail) {
        var quote = detail.quote || detail.citation || "";
        var match = findTextRange(text, quote);
        if (!match) return;
        pushRange(ranges, seen, {
          start: match.start,
          end: match.end,
          cardId: detail.card_id || "",
          examPointId: ep.id,
          title: ep.title || ep.id,
          citation: text.slice(match.start, match.end)
        });
      });
    });

    ranges.sort(function (a, b) {
      if (a.start !== b.start) return a.start - b.start;
      return (b.end - b.start) - (a.end - a.start);
    });

    if (options && options.raw) return ranges;
    return cleanHighlightRanges(ranges);
  }

  function getBadgeForExamPoints(eps) {
    if (!eps.length) return { cls: "", badge: "" };
    var hasConfirmed = eps.some(function (ep) { return ep.status === "confirmed"; });
    var hasTrapWarning = eps.some(function (ep) { return ep.display_layer === "trap_warning"; });
    var hasBasic = eps.every(function (ep) { return ep.display_layer === "basic_textbook"; });
    var qCount = eps.reduce(function (sum, ep) { return sum + (ep.question_ids || []).length; }, 0);
    var qaCount = eps.reduce(function (sum, ep) { return sum + (ep.qa_ids || []).length; }, 0);
    var hasQuestions = qCount > 0 || qaCount > 0;
    var needsReview = eps.some(function (ep) { return /^needs_/.test(ep.status || ""); });
    var priority = hasTrapWarning || hasQuestions || needsReview;
    var badge = "";
    if (qCount) badge += '<span class="ep-badge counts">题 ' + qCount + "</span>";
    if (qaCount) badge += '<span class="ep-badge counts">答疑 ' + qaCount + "</span>";
    if (hasTrapWarning) return { cls: "ep-needs-review", badge: '<span class="ep-badge review">易错</span>' + badge, priority: priority };
    if (hasQuestions) return { cls: hasConfirmed ? "ep-confirmed" : "ep-linked", badge: badge, priority: priority };
    if (needsReview) return { cls: "ep-needs-review", badge: '<span class="ep-badge review">待补证</span>', priority: priority };
    if (hasConfirmed) {
      return { cls: "ep-confirmed", badge: badge, priority: priority };
    }
    if (hasBasic) return { cls: "ep-basic", badge: '<span class="ep-badge basic">基础</span>', priority: priority };
    return { cls: "ep-candidate", badge: '<span class="ep-badge candidate">待看</span>', priority: priority };
  }

  function getExamPointBadge(state, cid) {
    return getBadgeForExamPoints(Store.getExamPointsForCard(state, cid));
  }

  function getParagraphExamPoints(paragraph, state, rawRanges) {
    var byId = {};
    U.unique((paragraph.highlightCardIds || []).concat(paragraph.cardIds || [])).forEach(function (cid) {
      Store.getExamPointsForCard(state, cid).forEach(function (ep) {
        if (ep && ep.id) byId[ep.id] = ep;
      });
    });
    (rawRanges || findHighlightRanges(paragraph, state, { raw: true })).forEach(function (range) {
      var ep = range.examPointId ? state.examPointById[range.examPointId] : null;
      if (ep && ep.id) byId[ep.id] = ep;
    });
    return Object.keys(byId).map(function (id) { return byId[id]; });
  }

  function getMarginalNotes(paragraph, state, rawRanges) {
    var eps = getParagraphExamPoints(paragraph, state, rawRanges);
    var notes = [];
    var seen = {};

    function getTotalSourceCount(ep) {
      var ids = [];
      if (!ep) return 0;
      ids = ids.concat(ep.source_card_ids || [], ep.external_source_card_ids || []);
      (ep.source_card_details || []).forEach(function (detail) {
        if (detail.card_id) ids.push(detail.card_id);
      });
      (ep.external_source_card_details || []).forEach(function (detail) {
        if (detail.card_id) ids.push(detail.card_id);
      });
      ids = U.unique(ids.filter(Boolean));
      if (ids.length) return ids.length;
      return ((ep.source_card_details || []).length + (ep.external_source_card_details || []).length);
    }

    function addLine(lines, label, text) {
      if (!text) return;
      var value = String(text).trim();
      if (!value) return;
      var exists = lines.some(function (line) {
        return line.label === label && line.text === value;
      });
      if (!exists) lines.push({ label: label, text: value });
    }

    function addNote(ep, qCount, qaCount) {
      var title = ep.title || ep.id;
      var trapText = ep.student_confusion || (ep.display_layer === "trap_warning" ? title : "");
      var hasTrap = !!trapText;
      var sourceCount = getTotalSourceCount(ep);
      var lines = [];
      if (qCount) addLine(lines, "题目", qCount + " 道关联题");
      if (qaCount) addLine(lines, "答疑", qaCount + " 条学生常问");
      if (sourceCount) addLine(lines, "原文", sourceCount + " 条原文依据");
      if (!qCount && !qaCount && !hasTrap) return;

      var key = ep.id || title;
      if (seen[key]) return;
      seen[key] = true;
      var kind = hasTrap ? "trap" : (qaCount ? "qa" : (qCount ? "method" : "exam"));
      notes.push({
        kind: kind,
        label: hasTrap ? "高频考点 · 易错" : (qCount ? "高频考点" : "学生常问"),
        text: title,
        lines: lines,
        examPointId: ep.id,
        title: title,
        quote: ((ep.source_card_details || [])[0] || {}).quote || "",
        questionCount: qCount,
        qaCount: qaCount
      });
    }

    eps.forEach(function (ep) {
      var qCount = (ep.question_ids || []).length + (ep.option_bindings || []).length;
      var qaCount = (ep.qa_ids || []).length;
      addNote(ep, qCount, qaCount);
    });

    return notes.slice(0, 3);
  }

  function shouldShowAnnotation(epInfo, mode) {
    if (!epInfo.cls) return false;
    if (mode !== "priority") return true;
    return !!epInfo.priority;
  }

  function renderParagraph(paragraph, state, mode, rawRanges) {
    var text = paragraph.text || "";
    var ranges = cleanHighlightItems((rawRanges || findHighlightRanges(paragraph, state, { raw: true })).map(function (range) {
      var card = state.cardById[range.cardId] || {};
      var ep = range.examPointId ? state.examPointById[range.examPointId] : null;
      var epInfo = ep ? getBadgeForExamPoints([ep]) : getExamPointBadge(state, range.cardId);
      return {
        card: card,
        epInfo: epInfo,
        range: range
      };
    }).filter(function (item) {
      return shouldShowAnnotation(item.epInfo, mode || "priority");
    }));
    if (!ranges.length) return U.escapeHtml(text);

    var html = "";
    var cursor = 0;
    ranges.forEach(function (item) {
      var range = item.range;
      var card = item.card;
      var epInfo = item.epInfo;
      html += U.escapeHtml(text.slice(cursor, range.start));
      html += '<span class="' + epInfo.cls + '"';
      if (range.examPointId) {
        html += ' data-exam-point="' + U.escapeHtml(range.examPointId) + '"';
      } else {
        html += ' data-card="' + U.escapeHtml(range.cardId) + '"';
      }
      html += ' title="' + U.escapeHtml(range.title || card.knowledge || range.cardId) + '">';
      html += U.escapeHtml(text.slice(range.start, range.end)) + epInfo.badge;
      html += "</span>";
      cursor = range.end;
    });
    html += U.escapeHtml(text.slice(cursor));
    return html;
  }

  function renderToc(state, handlers) {
    var toc = U.byId("tocList");
    if (!toc) return;
    toc.innerHTML = "";

    (state.chapter.sections || []).forEach(function (section) {
      var wrap = document.createElement("div");
      wrap.className = "toc-section" + (section.is_appendix ? " toc-section-appendix" : "");

      var sectionButton = document.createElement("button");
      sectionButton.type = "button";
      sectionButton.className = "toc-section-title";
      sectionButton.textContent = section.display_title || (section.section_id + " " + section.section_title);
      sectionButton.addEventListener("click", function () {
        handlers.scrollToElement("sec-" + section.section_id);
      });
      wrap.appendChild(sectionButton);

      (section.subsections || []).forEach(function (subsection, index) {
        if (!subsection.title) return;
        var subButton = document.createElement("button");
        subButton.type = "button";
        subButton.className = "toc-subtitle";
        subButton.textContent = subsection.display_title || subsection.title;
        subButton.addEventListener("click", function () {
          handlers.scrollToElement(makeSubId(section.section_id, index));
        });
        wrap.appendChild(subButton);
      });

      toc.appendChild(wrap);
    });
  }

  function renderReader(state, handlers, options) {
    options = options || {};
    var annotationMode = options.annotationMode || "priority";
    var reader = U.byId("reader");
    if (!reader) return;
    reader.innerHTML = "";

    var content = document.createElement("article");
    content.className = "reader-content";
    content.innerHTML = '<h1 class="chapter-title">' + U.escapeHtml(state.chapter.chapter || "CAMS v6.51 教材") + "</h1>";
    var paragraphCursor = 0;

    (state.chapter.sections || []).forEach(function (section) {
      var sectionEl = document.createElement("section");
      sectionEl.className = "reader-section" + (section.is_appendix ? " reader-appendix" : "");
      sectionEl.id = "sec-" + section.section_id;
      sectionEl.innerHTML = '<h2>' + U.escapeHtml(section.display_title || (section.section_id + " " + section.section_title)) + "</h2>";

      (section.subsections || []).forEach(function (subsection, subIndex) {
        var subEl = document.createElement("section");
        subEl.className = "reader-subsection";
        if (subsection.title) {
          subEl.id = makeSubId(section.section_id, subIndex);
          var h3 = document.createElement("h3");
          h3.textContent = subsection.display_title || subsection.title;
          subEl.appendChild(h3);
        }

        (subsection.paragraphs || []).forEach(function (paragraph) {
          var isAppendix = !!(section.is_appendix || subsection.is_appendix || paragraph.is_appendix);
          var row = document.createElement("div");
          row.className = "reader-note-row" + (isAppendix ? " appendix-note-row" : "");
          var p = document.createElement("p");
          p.className = "reader-paragraph";
          var paraData = {
            text: paragraph.text || "",
            cardIds: paragraph.card_ids || [],
            highlightCardIds: paragraph.highlight_card_ids || []
          };
          var rawRanges = isAppendix ? [] : findHighlightRanges(paraData, state, { raw: true });
          var paraInfo = state.paragraphs[paragraphCursor];
          paragraphCursor += 1;
          if (paraInfo) p.id = paraInfo.id;
          row.setAttribute("data-paragraph-id", paraInfo ? paraInfo.id : "");
          p.setAttribute("data-cards", (paragraph.card_ids || []).join(","));
          p.innerHTML = renderParagraph(paraData, state, annotationMode, rawRanges);
          row.appendChild(p);

          var notes = isAppendix ? [] : getMarginalNotes(paraData, state, rawRanges);
          if (notes.length) {
            row.dataset.notes = JSON.stringify(notes);
            var noteWrap = document.createElement("div");
            noteWrap.className = "margin-notes";
            notes.forEach(function (note) {
              var noteButton = document.createElement("button");
              noteButton.type = "button";
              noteButton.className = "margin-note note-" + note.kind;
              if (note.examPointId) noteButton.setAttribute("data-exam-point", note.examPointId);
              var noteHtml = '<span class="margin-note-kicker">' + U.escapeHtml(note.label) + '</span><strong class="margin-note-title">' + U.escapeHtml(U.shortText(note.text, 58)) + "</strong>";
              if ((note.lines || []).length) {
                noteHtml += '<span class="margin-note-lines">';
                note.lines.slice(0, 3).forEach(function (line) {
                  noteHtml += '<span class="margin-note-line"><em>' + U.escapeHtml(line.label) + '</em>' + U.escapeHtml(U.shortText(line.text, 70)) + "</span>";
                });
                noteHtml += "</span>";
              }
              noteButton.innerHTML = noteHtml;
              noteWrap.appendChild(noteButton);
            });
            row.appendChild(noteWrap);
          }

          subEl.appendChild(row);
        });

        sectionEl.appendChild(subEl);
      });

      content.appendChild(sectionEl);
    });

    reader.appendChild(content);
    if (!reader._camsReaderClickBound) {
      reader.addEventListener("click", function (event) {
        var target = event.target.closest(".ep-basic, .ep-linked, .ep-needs-review, .ep-candidate, .ep-confirmed, .highlight, .margin-note");
        if (!target) return;
        var epId = target.getAttribute("data-exam-point");
        if (epId && handlers.selectExamPoint) {
          handlers.selectExamPoint(epId, { source: "reader" });
          return;
        }
        handlers.selectCard(target.getAttribute("data-card"), { scroll: false, source: "reader" });
      });
      reader._camsReaderClickBound = true;
    }
    if (!reader._camsReaderScrollBound) {
      reader.addEventListener("scroll", function () {
        window.clearTimeout(reader._camsVisibleNotesTimer);
        reader._camsVisibleNotesTimer = window.setTimeout(function () {
          notifyVisibleNotes(handlers);
        }, 120);
      });
      reader._camsReaderScrollBound = true;
    }

    renderToc(state, handlers);
    window.setTimeout(function () {
      notifyVisibleNotes(handlers);
    }, 0);
  }

  function notifyVisibleNotes(handlers) {
    if (!handlers || !handlers.updateVisibleNotes) return;
    var reader = U.byId("reader");
    if (!reader) return;
    var readerRect = reader.getBoundingClientRect();
    var rows = Array.prototype.slice.call(reader.querySelectorAll(".reader-note-row[data-notes]"));
    var notes = [];
    var seen = {};
    rows.forEach(function (row) {
      var rect = row.getBoundingClientRect();
      if (rect.bottom < readerRect.top + 70 || rect.top > readerRect.bottom - 80) return;
      try {
        JSON.parse(row.dataset.notes || "[]").forEach(function (note) {
          var key = note.kind + "|" + (note.examPointId || note.text);
          if (seen[key]) return;
          seen[key] = true;
          notes.push(note);
        });
      } catch (error) {
        // Ignore malformed note payloads; the reader remains usable.
      }
    });
    handlers.updateVisibleNotes(notes.slice(0, 8));
  }

  function clearActive() {
    document.querySelectorAll(".ep-basic.active, .ep-linked.active, .ep-needs-review.active, .ep-candidate.active, .ep-confirmed.active, .highlight.active").forEach(function (el) {
      el.classList.remove("active");
    });
    document.querySelectorAll(".reader-paragraph.flash").forEach(function (el) {
      el.classList.remove("flash");
    });
  }

  function scrollToElement(id) {
    var el = U.byId(id);
    if (!el) return false;
    el.scrollIntoView({ block: "start", behavior: "auto" });
    return true;
  }

  function scrollToCard(state, cid) {
    clearActive();
    var el = null;
    var reader = U.byId("reader") || document;
    reader.querySelectorAll("[data-card]").forEach(function (node) {
      if (!el && node.getAttribute("data-card") === cid) el = node;
    });
    if (!el) {
      var paragraph = state.paragraphByCard[cid];
      if (paragraph) el = U.byId(paragraph.id);
    }
    if (!el) return false;

    if (el.classList.contains("ep-basic") || el.classList.contains("ep-linked") || el.classList.contains("ep-needs-review") || el.classList.contains("ep-candidate") || el.classList.contains("ep-confirmed") || el.classList.contains("highlight")) {
      el.classList.add("active");
    } else {
      el.classList.add("flash");
      window.setTimeout(function () { el.classList.remove("flash"); }, 1600);
    }
    el.scrollIntoView({ block: "center", behavior: "auto" });
    return true;
  }

  function scrollToParagraph(id) {
    clearActive();
    var el = U.byId(id);
    if (!el) return false;
    el.classList.add("flash");
    el.scrollIntoView({ block: "center", behavior: "auto" });
    window.setTimeout(function () { el.classList.remove("flash"); }, 1600);
    return true;
  }

  window.CamsReader = {
    render: renderReader,
    scrollToCard: scrollToCard,
    scrollToElement: scrollToElement,
    scrollToParagraph: scrollToParagraph
  };
})();
