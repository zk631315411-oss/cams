(function () {
  var U = window.CamsUtils;

  function cardHits(state, query) {
    return state.cards.map(function (card) {
      var score = U.scoreText(card.knowledge, query) + U.scoreText(card.citation, query) * 0.6;
      return { type: "card", score: score, card: card };
    }).filter(function (item) {
      return item.score > 0;
    }).sort(function (a, b) {
      return b.score - a.score;
    }).slice(0, 12);
  }

  function questionHits(state, query) {
    return state.questions.map(function (question) {
      var options = question.options ? Object.keys(question.options).map(function (key) {
        return question.options[key];
      }).join(" ") : "";
      var score = U.scoreText(question.stem, query) + U.scoreText(options, query) * 0.7;
      return { type: "question", score: score, question: question };
    }).filter(function (item) {
      return item.score > 0;
    }).sort(function (a, b) {
      return b.score - a.score;
    }).slice(0, 10);
  }

  function trapHits(state, query) {
    var rows = [];
    state.examPoints.forEach(function (ep) {
      var text = [ep.title, ep.student_confusion].join(" ");
      var score = U.scoreText(text, query);
      if (score > 0 && (ep.student_confusion || ep.display_layer === "trap_warning")) {
        rows.push({ type: "trap", score: score, examPoint: ep });
      }
    });
    state.optionEvidence.forEach(function (mapping) {
      (mapping.options || []).forEach(function (option) {
        var score = U.scoreText(option.common_trap, query) + U.scoreText(option.option_text, query) * 0.5;
        if (score > 0 && option.common_trap) {
          rows.push({ type: "trap-option", score: score, mapping: mapping, option: option });
        }
      });
    });
    return rows.sort(function (a, b) {
      return b.score - a.score;
    }).slice(0, 8);
  }

  function examPointHits(state, query) {
    return state.examPoints.map(function (ep) {
      var body = [
        ep.title,
        ep.type,
        ep.status,
        ep.student_confusion,
        ep.reason,
        (ep.question_ids || []).join(" ")
      ].join(" ");
      var score = U.scoreText(body, query);
      return { type: "exam-point", score: score, examPoint: ep };
    }).filter(function (item) {
      return item.score > 0;
    }).sort(function (a, b) {
      return b.score - a.score;
    }).slice(0, 8);
  }

  function paragraphHits(state, query) {
    return state.paragraphs.map(function (paragraph) {
      var score = U.scoreText(paragraph.text, query);
      return { type: "paragraph", score: score, paragraph: paragraph };
    }).filter(function (item) {
      return item.score > 0;
    }).sort(function (a, b) {
      return b.score - a.score;
    }).slice(0, 8);
  }

  function section(title, count) {
    return '<div class="search-section-title">' + U.escapeHtml(title) + " (" + count + ")</div>";
  }

  function renderTabs(active, counts) {
    var tabs = [
      { id: "all", label: "全部" },
      { id: "questions", label: "题目" },
      { id: "exam-points", label: "考点" },
      { id: "traps", label: "易错" },
      { id: "text", label: "原文" }
    ];
    var html = '<div class="search-tabs">';
    tabs.forEach(function (tab) {
      html += '<button class="search-tab' + (active === tab.id ? " active" : "") + '" type="button" data-search-tab="' + U.escapeHtml(tab.id) + '">';
      html += U.escapeHtml(tab.label);
      if (counts && typeof counts[tab.id] === "number") html += '<span>' + counts[tab.id] + "</span>";
      html += "</button>";
    });
    html += "</div>";
    return html;
  }

  function renderTrapHit(hit, query) {
    if (hit.type === "trap-option") {
      return '<button class="search-hit" type="button" data-kind="question" data-id="' + U.escapeHtml(hit.mapping.question_id) + '">' +
        '<div class="search-hit-title"><span class="pill red">易错</span><span>' + U.escapeHtml(U.shortText(hit.option.option_text || hit.mapping.question_id, 82)) + "</span></div>" +
        '<div class="search-hit-snippet">' + U.makeSnippet(hit.option.common_trap || "", query, 130) + "</div></button>";
    }
    return '<button class="search-hit" type="button" data-kind="exam-point" data-id="' + U.escapeHtml(hit.examPoint.id) + '">' +
      '<div class="search-hit-title"><span class="pill red">易错</span><span>' + U.escapeHtml(U.shortText(hit.examPoint.title || hit.examPoint.id, 82)) + "</span></div>" +
      '<div class="search-hit-snippet">' + U.makeSnippet(hit.examPoint.student_confusion || "", query, 130) + "</div></button>";
  }

  function render(state, query, activeTab) {
    activeTab = activeTab || "all";
    var cards = cardHits(state, query);
    var questions = questionHits(state, query);
    var examPoints = examPointHits(state, query);
    var traps = trapHits(state, query);
    var paragraphs = paragraphHits(state, query);
    var html = "";
    var counts = {
      all: cards.length + questions.length + examPoints.length + traps.length + paragraphs.length,
      questions: questions.length,
      "exam-points": examPoints.length,
      traps: traps.length,
      text: paragraphs.length + cards.length
    };

    if (!counts.all) {
      return '<div class="notice">未找到匹配结果</div>';
    }
    html += renderTabs(activeTab, counts);

    if ((activeTab === "all" || activeTab === "questions") && questions.length) {
      html += section("题目", questions.length);
      questions.forEach(function (hit) {
        html += '<button class="search-hit" type="button" data-kind="question" data-id="' + U.escapeHtml(hit.question.id) + '">';
        html += '<div class="search-hit-title"><span class="pill amber">题目</span><span>' + U.escapeHtml(U.shortText(hit.question.stem || hit.question.id, 82)) + "</span></div>";
        html += '<div class="search-hit-snippet">答案 ' + U.escapeHtml(hit.question.answer || "") + "</div>";
        html += "</button>";
      });
    }

    if ((activeTab === "all" || activeTab === "exam-points") && examPoints.length) {
      html += section("考点", examPoints.length);
      examPoints.forEach(function (hit) {
        html += '<button class="search-hit" type="button" data-kind="exam-point" data-id="' + U.escapeHtml(hit.examPoint.id) + '">';
        html += '<div class="search-hit-title"><span class="pill green">考点</span><span>' + U.escapeHtml(U.shortText(hit.examPoint.title || hit.examPoint.id, 82)) + "</span></div>";
        html += '<div class="search-hit-snippet">关联题目 ' + U.escapeHtml((hit.examPoint.question_ids || []).join("、") || "无") + "</div>";
        html += "</button>";
      });
    }

    if ((activeTab === "all" || activeTab === "traps") && traps.length) {
      html += section("易错点", traps.length);
      traps.forEach(function (hit) {
        html += renderTrapHit(hit, query);
      });
    }

    if ((activeTab === "all" || activeTab === "text") && paragraphs.length) {
      html += section("原文", paragraphs.length);
      paragraphs.forEach(function (hit) {
        html += '<button class="search-hit" type="button" data-kind="paragraph" data-id="' + U.escapeHtml(hit.paragraph.id) + '">';
        html += '<div class="search-hit-title"><span class="pill">原文</span><span>' + U.escapeHtml(hit.paragraph.sectionId + " " + hit.paragraph.subsectionTitle) + "</span></div>";
        html += '<div class="search-hit-snippet">' + U.makeSnippet(hit.paragraph.text, query, 130) + "</div>";
        html += "</button>";
      });
    }

    if ((activeTab === "text") && cards.length) {
      html += section("教材原文摘录", cards.length);
      cards.forEach(function (hit) {
        html += '<button class="search-hit" type="button" data-kind="card" data-id="' + U.escapeHtml(hit.card.card_id) + '">';
        html += '<div class="search-hit-title"><span class="pill blue">原文</span><span>' + U.escapeHtml(U.shortText(hit.card.knowledge || hit.card.citation || "教材原文", 70)) + "</span></div>";
        html += '<div class="search-hit-snippet">' + U.makeSnippet(hit.card.citation || "", query, 110) + "</div>";
        html += "</button>";
      });
    }

    return html;
  }

  function bind(state, handlers) {
    var input = U.byId("searchInput");
    var drop = U.byId("searchResults");
    if (!input || !drop) return;
    var timer = null;
    var activeTab = "all";

    function close() {
      U.setHidden(drop, true);
    }

    function update() {
      var query = input.value.trim();
      window.clearTimeout(timer);
      if (query.length < 2) {
        drop.innerHTML = "";
        close();
        return;
      }
      timer = window.setTimeout(function () {
        drop.innerHTML = render(state, query, activeTab);
        U.setHidden(drop, false);
      }, 120);
    }

    input.addEventListener("input", update);
    input.addEventListener("focus", function () {
      if (input.value.trim().length >= 2) update();
    });

    drop.addEventListener("mousedown", function (event) {
      var tab = event.target.closest("[data-search-tab]");
      if (tab) {
        event.preventDefault();
        activeTab = tab.getAttribute("data-search-tab") || "all";
        drop.innerHTML = render(state, input.value.trim(), activeTab);
        U.setHidden(drop, false);
        return;
      }
      var hit = event.target.closest(".search-hit");
      if (!hit) return;
      event.preventDefault();
      var kind = hit.getAttribute("data-kind");
      var id = hit.getAttribute("data-id");
      input.blur();
      close();
      if (kind === "card") handlers.selectCard(id, { scroll: true });
      if (kind === "question") handlers.selectQuestion(id);
      if (kind === "exam-point" && handlers.selectExamPoint) handlers.selectExamPoint(id);
      if (kind === "paragraph") handlers.scrollToParagraph(id);
    });

    document.addEventListener("click", function (event) {
      if (!event.target.closest(".search-box")) close();
    });
  }

  window.CamsSearch = {
    bind: bind
  };
})();
