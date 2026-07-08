(function () {
  var U = window.CamsUtils;
  var Store = window.CamsStore;

  function pill(text, cls) {
    if (!text) return "";
    return '<span class="pill ' + (cls || "") + '">' + U.escapeHtml(text) + "</span>";
  }

  function empty(text) {
    return '<div class="notice">' + U.escapeHtml(text || "暂无数据") + "</div>";
  }

  function getPane() {
    return U.byId("detailContent") || U.byId("detailPane");
  }

  function renderPanelHeadStart(options) {
    var html = '<div class="panel-head"><div class="panel-card-head">';
    if (options && options.canGoBack) {
      html += '<button class="panel-back-button" type="button" data-panel-back aria-label="返回上一步">‹ 返回</button>';
    }
    return html;
  }

  function bindBackEvent(pane, handlers) {
    var button = pane && pane.querySelector("[data-panel-back]");
    if (!button) return;
    button.onclick = function (event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      if (handlers.goBack) handlers.goBack();
      return false;
    };
  }

  function getQuestionConcepts(state, questionId) {
    var mapping = state.questionMap[questionId] || {};
    var sections = (mapping.matched_card_ids || []).map(function (cid) {
      return state.cardToSection[cid];
    }).filter(Boolean);
    return U.unique(sections);
  }

  function getQuestionProfile(state, question) {
    var evidence = Store.getOptionEvidenceForQuestion(state, question.id);
    var options = evidence && evidence.options ? evidence.options : [];
    var quality = evidence && evidence.quality ? evidence.quality : {};
    return {
      evidence: evidence,
      quality: quality,
      hasEvidence: !!evidence,
      hasTrap: options.some(function (option) { return !!option.common_trap; }),
      hasIssues: !!(evidence && ((evidence.validation_issues || []).length || (evidence.source_data_issues || []).length)),
      hasNoneEvidence: !!(evidence && (quality.none_evidence_options || 0) > 0)
    };
  }

  function getExamPointPriority(ep) {
    var qCount = (ep.question_ids || []).length;
    var qaCount = (ep.qa_ids || []).length;
    var status = ep.status || "";
    if (status === "needs_teacher_attention" || ep.display_layer === "trap_warning" || ep.student_confusion) return "trap";
    if (status === "needs_evidence" || status === "needs_manual" || status === "needs_question_binding") return "review";
    if (qCount || qaCount || (ep.option_bindings || []).length) return "linked";
    return "candidate";
  }

  function evidenceQualityText(mapping) {
    if (!mapping) return "还没有生成教材依据";
    var quality = mapping.quality || {};
    var direct = quality.direct_evidence_options || 0;
    var indirect = quality.indirect_evidence_options || 0;
    var none = quality.none_evidence_options || 0;
    var text = [];
    if (direct) text.push(direct + " 个选项有明确原文");
    if (indirect) text.push(indirect + " 个选项需要结合上下文");
    if (none) text.push(none + " 个选项还缺依据");
    return text.length ? text.join("，") : "已生成教材依据，待教研复核";
  }

  function questionDirectoryEvidenceText(mapping) {
    if (!mapping) return "待补依据";
    var quality = mapping.quality || {};
    if ((quality.none_evidence_options || 0) > 0) return "部分选项需补依据";
    if ((quality.indirect_evidence_options || 0) > 0) return "部分选项需结合上下文";
    return "依据较完整";
  }

  function teacherText(value) {
    return String(value || "")
      .replace(/教材?句卡\s*[A-Za-z0-9_-]+/g, "教材原文")
      .replace(/句卡\s*[A-Za-z0-9_-]+/g, "教材原文")
      .replace(/\b(?:v\d+[a-z]?|ch\d+s?)_[A-Za-z]*\d+\b/gi, "教材原文")
      .replace(/[A-Za-z]*v\d+s?_N\d+/gi, "教材原文")
      .replace(/教材?句卡/g, "教材原文")
      .replace(/句卡/g, "教材原文")
      .replace(/(?:原文)?教材原文(?:教材原文|原文)+/g, "教材原文")
      .replace(/原文教材原文/g, "教材原文")
      .replace(/\s+/g, " ")
      .trim();
  }

  function confidenceLabel(value) {
    var key = String(value || "").toLowerCase().trim();
    var labels = {
      high: "高",
      medium: "中",
      low: "低",
      insufficient: "证据不足"
    };
    return labels[key] || String(value || "证据不足");
  }

  function cleanQuestionDisplay(value) {
    return teacherText(value)
      .replace(/\b[A-Za-z][A-Za-z0-9'’,.-]*(?:\s+[A-Za-z][A-Za-z0-9'’,.-]*){2,}[?.]?/g, "")
      .replace(/\s+([A-E])\s*(?=[\u4e00-\u9fa5])/g, " $1")
      .replace(/\s+/g, " ")
      .trim();
  }

  function getCardPageLabel(state, card) {
    var cid = typeof card === "string" ? card : ((card && (card.card_id || card.id)) || "");
    if (!cid) return "";
    if (card && card.page_label) return String(card.page_label || "");
    var page = state && state.cardPageMap && state.cardPageMap[cid];
    return page && page.page_label ? String(page.page_label) : "";
  }

  function renderPageLabelSuffix(state, card) {
    var label = getCardPageLabel(state, card);
    return label ? " · " + U.escapeHtml(label) : "";
  }

  function evidenceDisplayName(state, card, fallback) {
    var label = getCardPageLabel(state, card);
    return label ? (fallback || "教材原文") + " · " + label : (fallback || "教材原文");
  }

  function splitStructuredItems(value, limit) {
    var text = teacherText(value)
      .replace(/[；;]/g, "。")
      .replace(/。\s*/g, "。|")
      .replace(/：\s*/g, "：");
    var items = text.split("|").map(function (item) {
      return item.replace(/^。+|。+$/g, "").trim();
    }).filter(function (item) {
      return item && item.length > 1;
    });
    if (items.length <= 1 && text.length > 120) {
      items = text.replace(/[，,]/g, "，|").split("|").map(function (item) {
        return item.replace(/^，+|，+$/g, "").trim();
      }).filter(Boolean);
    }
    return items.slice(0, limit || 6);
  }

  function renderStructuredNote(value, cls, emptyText) {
    var items = splitStructuredItems(value, 6);
    if (!items.length) {
      return '<p class="' + U.escapeHtml(cls || "structured-note") + '">' + U.escapeHtml(emptyText || "") + "</p>";
    }
    if (items.length === 1) {
      return '<p class="' + U.escapeHtml(cls || "structured-note") + '">' + U.escapeHtml(items[0]) + "</p>";
    }
    var html = '<ul class="' + U.escapeHtml(cls || "structured-note-list") + '">';
    items.forEach(function (item) {
      html += '<li>' + U.escapeHtml(item) + "</li>";
    });
    html += "</ul>";
    return html;
  }
  function polishQaReplyItem(item) {
    var text = teacherText(item).replace(/([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])/g, "$1$2");
    if (text && !/[。！？；：.!?）)”]$/.test(text)) text += "。";
    return text;
  }

  function renderQaReplyAnalysis(reply) {
    var text = teacherText(reply || "").replace(/(^|\s)(解析|总结|选项分析)(?=\s)/g, "$1$2：");
    if (!text) return "";
    var sentences = splitStructuredItems(text, 120).map(polishQaReplyItem).filter(function (item) {
      return item && item.length > 3;
    });
    if (!sentences.length) {
      return '<p class="qa-reply-paragraph">' + U.escapeHtml(text) + "</p>";
    }

    var conclusion = sentences[0];
    var explanation = sentences.slice(1).filter(function (item) {
      return !/^选\s*项$/.test(item) && !/^(内容|分析|结论|阶段归属)$/.test(item);
    });
    var html = '<div class="qa-reply-structured">';
    html += '<div class="qa-reply-lead"><strong>结论</strong><p>' + U.escapeHtml(conclusion) + '</p></div>';
    if (explanation.length) {
      html += '<div class="qa-reply-body"><strong>说明</strong>';
      explanation.forEach(function (item) {
        html += '<p>' + U.escapeHtml(item) + '</p>';
      });
      html += '</div>';
    }
    html += '</div>';
    return html;
  }

  function renderFilterBar(type, filters, active) {
    var html = '<div class="filter-bar">';
    filters.forEach(function (filter) {
      html += '<button class="filter-chip' + (active === filter.id ? " active" : "") + '" type="button" data-' + type + '-filter="' + U.escapeHtml(filter.id) + '">';
      html += U.escapeHtml(filter.label);
      if (typeof filter.count === "number") html += '<span>' + filter.count + "</span>";
      html += "</button>";
    });
    html += "</div>";
    return html;
  }

  function bindFilterEvents(pane, handlers) {
    pane.querySelectorAll("[data-question-filter]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (handlers.showQuestionList) handlers.showQuestionList(button.getAttribute("data-question-filter"));
      });
    });
    pane.querySelectorAll("[data-exam-filter]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (handlers.showExamPointList) handlers.showExamPointList(button.getAttribute("data-exam-filter"));
      });
    });
    pane.querySelectorAll("[data-home-action]").forEach(function (button) {
      button.addEventListener("click", function () {
        var action = button.getAttribute("data-home-action");
        if (action === "questions" && handlers.showQuestionList) handlers.showQuestionList(button.getAttribute("data-question-filter") || "all");
        if (action === "exam-points" && handlers.showExamPointList) handlers.showExamPointList(button.getAttribute("data-exam-filter") || "priority");
      });
    });
  }

  function bindWorkflowEvents(pane, handlers) {
    pane.querySelectorAll("[data-workflow-run]").forEach(function (button) {
      button.addEventListener("click", function () {
        var input = U.byId("workflowInput");
        if (handlers.runWorkflow) handlers.runWorkflow(button.getAttribute("data-workflow-run"), input ? input.value : "");
      });
    });
    pane.querySelectorAll("[data-new-question-draft]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (handlers.loadNewQuestionDraft) handlers.loadNewQuestionDraft(button.getAttribute("data-new-question-draft"));
      });
    });
    pane.querySelectorAll("[data-toggle-new-question-drafts]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (handlers.toggleNewQuestionDraftHistory) handlers.toggleNewQuestionDraftHistory();
      });
    });
    pane.querySelectorAll("[data-delete-new-question-draft]").forEach(function (button) {
      button.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();
        if (handlers.deleteNewQuestionDraft) handlers.deleteNewQuestionDraft(button.getAttribute("data-delete-new-question-draft"));
      });
    });
    pane.querySelectorAll("[data-refresh-new-question-drafts]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (handlers.refreshNewQuestionDrafts) handlers.refreshNewQuestionDrafts();
      });
    });
    pane.querySelectorAll("[data-student-qa-draft]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (handlers.loadStudentQaDraft) handlers.loadStudentQaDraft(button.getAttribute("data-student-qa-draft"));
      });
    });
    pane.querySelectorAll("[data-qa-group-more]").forEach(function (button) {
      button.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();
      });
    });
    pane.querySelectorAll("[data-toggle-student-qa-drafts]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (handlers.toggleStudentQaDraftHistory) handlers.toggleStudentQaDraftHistory();
      });
    });
    pane.querySelectorAll("[data-delete-student-qa-draft]").forEach(function (button) {
      button.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();
        if (handlers.deleteStudentQaDraft) handlers.deleteStudentQaDraft(button.getAttribute("data-delete-student-qa-draft"));
      });
    });
    pane.querySelectorAll("[data-refresh-student-qa-drafts]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (handlers.refreshStudentQaDrafts) handlers.refreshStudentQaDrafts();
      });
    });
    pane.querySelectorAll("[data-toggle-student-qa-evidence]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (handlers.toggleStudentQaEvidence) handlers.toggleStudentQaEvidence();
      });
    });
  }

  var STATUS_LABELS = {
    ai_candidate: "待确认",
    confirmed: "已确认",
    rejected: "已拒绝",
    needs_evidence: "缺证据",
    needs_manual: "需人工",
    needs_teacher_attention: "易错关注",
    needs_merge: "待合并",
    needs_split: "待拆分",
    needs_question_binding: "缺题目"
  };

  function examPointStatusLabel(status) {
    return STATUS_LABELS[status] || status || "待确认";
  }

  function renderFeedbackActions(ep) {
    var id = U.escapeHtml(ep.id);
    var html = '<div class="feedback-actions">';
    html += '<button class="fb-button confirm" type="button" data-fb-action="confirmed" data-fb-ep="' + id + '">确认考点</button>';
    html += '<button class="fb-button reject" type="button" data-fb-action="rejected" data-fb-ep="' + id + '">不是考点</button>';
    html += '<button class="fb-button" type="button" data-fb-action="needs_rename" data-fb-ep="' + id + '">需要改名</button>';
    html += '<button class="fb-button" type="button" data-fb-action="needs_merge" data-fb-ep="' + id + '">需要合并</button>';
    html += '<button class="fb-button" type="button" data-fb-action="needs_split" data-fb-ep="' + id + '">需要拆分</button>';
    html += '<button class="fb-button" type="button" data-fb-action="needs_evidence" data-fb-ep="' + id + '">缺教材证据</button>';
    html += '<button class="fb-button" type="button" data-fb-action="needs_question_binding" data-fb-ep="' + id + '">缺相关题</button>';
    html += "</div>";
    return html;
  }

  function getReaderSourceCount(ep) {
    return ((ep && ep.source_card_ids) || []).length;
  }

  function getExternalSourceCount(ep) {
    return ((ep && ep.external_source_card_ids) || []).length;
  }

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

  function renderSourceEvidenceText(ep) {
    var count = getTotalSourceCount(ep);
    return count ? count + " 条原文依据" : "0 条原文依据";
  }

  function renderExamPointEvidenceMeta(ep) {
    return '<span>' + U.escapeHtml(renderSourceEvidenceText(ep)) + "</span>";
  }

  function renderExamPointInlineMeta(state, ep) {
    var questions = Store.getQuestionsForExamPoint(state, ep);
    var qaCount = ((ep.qa_ids || []).length) || Store.getQaForExamPoint(state, ep).length;
    return [
      questions.length + " 道题",
      qaCount + " 条答疑",
      renderSourceEvidenceText(ep)
    ].join(" / ");
  }

  function renderQuestionOptions(question) {
    var keys = Object.keys(question.options || {}).sort();
    if (!keys.length) return "";
    var html = '<div class="question-options">';
    keys.forEach(function (key) {
      var correct = String(question.answer || "").indexOf(key) >= 0;
      html += '<div class="question-option' + (correct ? " correct" : "") + '">';
      html += '<strong>' + U.escapeHtml(key) + '</strong><span>' + U.escapeHtml(question.options[key]) + "</span>";
      html += "</div>";
    });
    html += "</div>";
    return html;
  }

  function renderQuestionCard(question, index, options) {
    var showOptions = !options || options.showOptions !== false;
    var showExplanation = options && options.showExplanation;
    var compactList = options && options.compactList;
    var state = options && options.state;
    var flags = (options && options.flags) || [];
    var evidence = state ? Store.getOptionEvidenceForQuestion(state, question.id) : null;
    var titlePrefix = typeof index === "number" ? (index + 1) + ". " : "";
    var html = '<button class="question-card' + (compactList ? " directory-question-card" : "") + '" type="button" data-question="' + U.escapeHtml(question.id) + '">';
    html += '<p class="question-title">' + titlePrefix + U.escapeHtml(question.stem || question.id) + "</p>";
    html += '<p class="question-meta">题号 ' + U.escapeHtml(question.id) + " · 答案 " + U.escapeHtml(question.answer || "") + "</p>";
    if (state) {
      html += '<div class="question-evidence-summary' + (compactList ? " compact-summary" : "") + '">' + (compactList ? questionDirectoryEvidencePill(evidence) : questionEvidencePill(evidence));
      if (evidence) html += '<span>' + U.escapeHtml(compactList ? questionDirectoryEvidenceText(evidence) : evidenceQualityText(evidence)) + "</span>";
      html += "</div>";
    }
    if (showOptions) html += renderQuestionOptions(question);
    if (showExplanation && question.explanation) {
      html += '<div class="question-explanation">' + U.escapeHtml(U.shortText(teacherText(question.explanation), 360)) + "</div>";
    }
    if (flags.length) {
      html += '<div class="question-flags">';
      flags.forEach(function (flag) {
        html += '<span class="' + U.escapeHtml(flag.cls || "") + '">' + U.escapeHtml(flag.label) + "</span>";
      });
      html += "</div>";
    }
    html += "</button>";
    return html;
  }

  function renderExamPointQuestions(state, ep, showExplanation) {
    var questions = Store.getQuestionsForExamPoint(state, ep);
    if (!questions.length) {
      return '<div class="panel-section"><div class="panel-section-header">相关题目</div>' +
        '<div class="panel-section-body">' + empty("这个考点暂时没有相关题。") + "</div></div>";
    }

    var html = '<div class="panel-section"><div class="panel-section-header">相关题目 · ' + questions.length + " 题</div>";
    questions.forEach(function (question, index) {
      html += renderQuestionCard(question, index, { showOptions: true, showExplanation: !!showExplanation });
    });
    html += "</div>";
    return html;
  }

  function renderDirectoryExamPointMeta(state, ep) {
    var questions = Store.getQuestionsForExamPoint(state, ep);
    return '<span class="exam-point-meta"><span>题目 ' + questions.length + '</span><span>答疑 ' + ((ep.qa_ids || []).length) + '</span>' + renderExamPointEvidenceMeta(ep) + '</span>';
  }

  function renderSmallExamPointCard(state, ep) {
    var priority = getExamPointPriority(ep);
    var html = '<button class="exam-point-card directory-card priority-' + U.escapeHtml(priority) + '" type="button" data-exam-point="' + U.escapeHtml(ep.id) + '">';
    html += '<p class="exam-point-title">' + U.escapeHtml(ep.title || ep.id) + "</p>";
    html += '<p class="exam-point-row-meta">' + renderDirectoryExamPointMeta(state, ep) + "</p>";
    html += "</button>";
    return html;
  }

  function renderMiniQuestionCard(state, question, index) {
    return renderQuestionCard(question, index, { showOptions: false, state: state });
  }

  function renderHomeMetric(label, value, action, filterAttr, filterValue) {
    var attr = filterAttr ? " " + filterAttr + '="' + U.escapeHtml(filterValue || "") + '"' : "";
    return '<button class="home-metric" type="button" data-home-action="' + U.escapeHtml(action || "") + '"' + attr + '>' +
      '<strong>' + U.escapeHtml(String(value)) + "</strong><span>" + U.escapeHtml(label) + "</span></button>";
  }

  function renderHandbookPoint(state, ep) {
    var questions = Store.getQuestionsForExamPoint(state, ep);
    var cards = Store.getCardsForExamPoint(state, ep);
    var quote = ((ep.source_card_details || [])[0] || {}).quote || (cards[0] && cards[0].citation) || "";
    var priority = getExamPointPriority(ep);
    var html = '<button class="handbook-point priority-' + U.escapeHtml(priority) + '" type="button" data-exam-point="' + U.escapeHtml(ep.id) + '">';
    html += '<span class="handbook-point-label">' + U.escapeHtml(priority === "trap" ? "易错" : (questions.length ? "高频考点" : "教材考点")) + "</span>";
    html += '<strong>' + U.escapeHtml(ep.title || ep.id) + "</strong>";
    if (quote) html += '<span class="handbook-quote">' + U.escapeHtml(U.shortText(quote, 96)) + "</span>";
    html += '<span class="handbook-meta">题目 ' + questions.length + " · 答疑 " + ((ep.qa_ids || []).length) + " · " + U.escapeHtml(ep.type || ep.teaching_point_type || "知识点") + "</span>";
    html += "</button>";
    return html;
  }

  function renderVisibleNote(note) {
    var html = '<button class="handbook-point note-' + U.escapeHtml(note.kind || "exam") + '" type="button" data-exam-point="' + U.escapeHtml(note.examPointId || "") + '">';
    html += '<span class="handbook-point-label">' + U.escapeHtml(note.label || "批注") + "</span>";
    html += '<strong>' + U.escapeHtml(note.title || note.text || "教材批注") + "</strong>";
    if (note.quote) html += '<span class="handbook-quote">' + U.escapeHtml(U.shortText(note.quote, 100)) + "</span>";
    if (note.text && note.text !== note.title) html += '<span class="handbook-note">' + U.escapeHtml(U.shortText(note.text, 120)) + "</span>";
    html += '<span class="handbook-meta">题目 ' + (note.questionCount || 0) + " · 答疑 " + (note.qaCount || 0) + "</span>";
    html += "</button>";
    return html;
  }

  function qaSectionSortKey(section) {
    var text = String(section || "unknown");
    var match = text.match(/(\d+)(?:\.(\d+))?/);
    if (!match) return 9999;
    return Number(match[1]) * 100 + Number(match[2] || 0);
  }

  function qaAnswerText(answer) {
    return String(answer || "")
      .toUpperCase()
      .replace(/[，,、\s]+/g, "、")
      .replace(/^、|、$/g, "");
  }

  function getQaQuestionContext(state, record) {
    var binding = Store.getQaBinding ? Store.getQaBinding(state, record.id) : null;
    var question = binding && binding.bound_question_id ? state.questionById[binding.bound_question_id] : null;
    var rawStem = question ? question.stem : (binding && binding.bound_question_stem) || record.question || record.id;
    var stem = cleanQuestionDisplay(rawStem)
      .replace(/^第二章\s*/i, "")
      .replace(/^\d+(?:\.\d+)?\s*/, "")
      .trim();
    var optionIndex = stem.search(/\s+[A-E][.、]?\s*/);
    if (optionIndex > 12) stem = stem.slice(0, optionIndex).trim();
    return {
      id: question ? question.id : ((binding && binding.bound_question_id) || ""),
      section: question ? question.section : ((binding && binding.bound_question_section) || record.section || ""),
      stem: stem,
      answer: qaAnswerText((question && question.answer) || record.answer),
      options: question ? question.options || {} : {}
    };
  }

  function getQaDisplaySection(state, record) {
    var context = getQaQuestionContext(state, record);
    return context.section || record.section || "unknown";
  }

  function getQaCleanLines(record) {
    return String(record.full_text || "")
      .split(/\r?\n/)
      .map(function (line) {
        return teacherText(line).replace(/^[Qq][：:]\s*/, "").trim();
      })
      .filter(Boolean);
  }

  function expandQaDoubtLine(lines, index) {
    var text = lines[index] || "";
    var questionMarkIndex = Math.max(text.lastIndexOf("？"), text.lastIndexOf("?"));
    var trailing = questionMarkIndex >= 0 ? text.slice(questionMarkIndex + 1).trim() : "";
    if (!trailing) return text;
    for (var i = index + 1; i < Math.min(lines.length, index + 3); i += 1) {
      var next = lines[i] || "";
      if (!next || /^\d+$/.test(next)) continue;
      if (/^(答案|正确答案|最终答案|解析|选项分析|核心分析思路|详细依据|结论|总结)/.test(next)) break;
      if (/^[A-E][.、\s]/i.test(next)) break;
      text += next;
      break;
    }
    return text;
  }

  function getQaStudentDoubt(record) {
    var lines = getQaCleanLines(record);
    var original = teacherText(record.question || "");
    var afterAnswer = false;
    var candidates = [];
    lines.forEach(function (line, index) {
      if (/^(答案|正确答案|最终答案)/.test(line) || /答案[：:]/.test(line)) afterAnswer = true;
      if (!/[？?]/.test(line)) return;
      if (line.length > 120) return;
      if (/^第二章/.test(line)) return;
      if (/^[A-E][.、\s]/i.test(line)) return;
      if (!afterAnswer && original.indexOf(line) >= 0) return;
      var hasStudentSignal = /(为什么|为何|怎么|如何|是否|不是|不选|理解|区别|选|错|对|指|意思)/.test(line);
      if (!afterAnswer && !hasStudentSignal) return;
      var text = expandQaDoubtLine(lines, index);
      candidates.push({
        text: U.shortText(text, 150),
        score: (afterAnswer ? 2 : 0) + (hasStudentSignal ? 2 : 0) + (/为什么/.test(line) ? 1 : 0)
      });
    });
    candidates.sort(function (a, b) { return b.score - a.score; });
    if (candidates[0]) return candidates[0].text;
    var answer = qaAnswerText(record.answer);
    if (answer) return "为什么这题选 " + answer + "？";
    return U.shortText(teacherText(record.question || "这道题应该怎么判断？"), 70);
  }

  function isLikelyQaTableStart(lines, index) {
    var line = lines[index] || "";
    var next = lines.slice(index, index + 10).join("");
    return (line === "选" && /(选项|项内容|内容阶段归属|阶段归属分析)/.test(next)) ||
      (/^选项$/.test(line) && /(内容|分析|结论|阶段归属)/.test(next));
  }

  function getQaReplyText(record, doubt) {
    var core = teacherText(record.core_point || "");
    var lines = getQaCleanLines(record);
    var start = -1;
    if (doubt) {
      lines.some(function (line, index) {
        if (line === doubt || line.indexOf(doubt) >= 0 || doubt.indexOf(line) >= 0) {
          start = index + 1;
          return true;
        }
        return false;
      });
    }
    if (start < 0) {
      lines.some(function (line, index) {
        if (/^(答案|正确答案|最终答案)/.test(line) || /答案[：:]/.test(line)) {
          start = index + 1;
          return true;
        }
        return false;
      });
    }

    var picked = [];
    for (var i = Math.max(start, 0); i < lines.length; i += 1) {
      var line = lines[i];
      if (!line || /^\d+$/.test(line)) continue;
      if (isLikelyQaTableStart(lines, i) && picked.length) break;
      if (/^(答案|正确答案|最终答案)/.test(line)) continue;
      if (doubt && (line === doubt || doubt.indexOf(line) >= 0 || line.indexOf(doubt) >= 0)) continue;
      if (/^第二章/.test(line) && picked.length) break;
      if (/[？?]/.test(line)) {
        if (!picked.length) continue;
        if (/^(为什么|为何|怎么|如何|是否|不是|不选|理解|区别)/.test(line)) break;
      }
      picked.push(line);
    }

    var extracted = teacherText(picked.join(" "));
    if (core && extracted && extracted.length > core.length + 80) return extracted;
    return core || extracted;
  }
  function renderQaCompactOptions(context, doubt) {
    var keys = Object.keys(context.options || {}).sort();
    if (!keys.length) return "";
    var relevant = {};
    String(context.answer || "").replace(/[A-E]/g, function (key) {
      relevant[key] = true;
      return key;
    });
    String(doubt || "").toUpperCase().replace(/[A-E]/g, function (key) {
      relevant[key] = true;
      return key;
    });
    var primaryKeys = keys.filter(function (key) { return relevant[key]; });
    var otherKeys = keys.filter(function (key) { return !relevant[key]; });
    if (!primaryKeys.length) {
      primaryKeys = keys.slice(0, Math.min(keys.length, 2));
      otherKeys = keys.slice(primaryKeys.length);
    }
    function renderRows(rowKeys) {
      return rowKeys.map(function (key) {
        var correct = String(context.answer || "").indexOf(key) >= 0;
        return '<span class="' + (correct ? "correct" : "") + '"><strong>' + U.escapeHtml(key) + "</strong>" + U.escapeHtml(context.options[key]) + "</span>";
      }).join("");
    }
    var html = '<div class="qa-compact-options">';
    html += renderRows(primaryKeys);
    if (otherKeys.length) {
      html += '<details class="qa-more-options"><summary>其他选项</summary>' + renderRows(otherKeys) + "</details>";
    }
    html += "</div>";
    return html;
  }

  function findQaOptionReason(lines, key, optionText) {
    function isOptionLine(value) {
      return /^(?:选项\s*)?[A-E](?:[.、\s：:]|(?=[\u4e00-\u9fa5]))/i.test(value || "");
    }
    var optionPattern = new RegExp("^(?:选项\\s*)?" + U.escapeRegExp(key) + "(?:[.、\\s：:]|(?=[\\u4e00-\\u9fa5]))", "i");
    var startIndex = 0;
    lines.some(function (line, index) {
      if (/^(答案|正确答案|最终答案)/.test(line) || /答案[：:]/.test(line) || /(为什么|怎么理解|选项分析)/.test(line)) {
        startIndex = index + 1;
        return true;
      }
      return false;
    });
    for (var i = startIndex; i < lines.length; i += 1) {
      var line = lines[i] || "";
      if (!optionPattern.test(line)) continue;
      if (/[？?]/.test(line) && !/^选项\s*[A-E]/i.test(line)) continue;
      var text = line.replace(optionPattern, "").trim();
      if (optionText && text === optionText) continue;
      if (optionText && text.indexOf(optionText) === 0) {
        text = text.slice(optionText.length).replace(/^[-—：:\s]+/, "").trim();
      }
      for (var j = i + 1; j < Math.min(lines.length, i + 4); j += 1) {
        var next = lines[j] || "";
        if (isOptionLine(next)) break;
        if (/^(解析|结论|总结|核心分析思路|详细依据)/.test(next)) break;
        if (/^[①②③④⑤]?\s*$/.test(next) || /^\d+$/.test(next)) continue;
        text += (text ? " " : "") + next;
        if (text.length > 180) break;
      }
      text = teacherText(text);
      if (text) return U.shortText(text, 190);
    }
    return "";
  }

  function renderQaOptionReasons(record, context) {
    var keys = Object.keys(context.options || {}).sort();
    if (!keys.length) return "";
    var lines = getQaCleanLines(record);
    var html = '<div class="qa-option-reason-list">';
    keys.forEach(function (key) {
      var correct = String(context.answer || "").indexOf(key) >= 0;
      var reason = findQaOptionReason(lines, key, context.options[key]);
      html += '<div class="qa-option-reason' + (correct ? " correct" : "") + '">';
      html += '<span>' + U.escapeHtml(key) + '</span><div>';
      html += '<strong>' + U.escapeHtml(correct ? "正确答案" : "排除项") + "</strong>";
      html += '<p>' + U.escapeHtml(reason || U.shortText(context.options[key] || "暂无单独说明。", 120)) + "</p>";
      html += "</div></div>";
    });
    html += "</div>";
    return html;
  }

  function renderQaStructuredRecord(record, context, doubt, reply, bodyText) {
    var html = '<div class="qa-record-structured">';
    html += '<div class="qa-record-block qa-record-emphasis"><span>学生真正卡住的点</span><p>' + U.escapeHtml(doubt) + "</p></div>";
    if (reply) {
      html += '<div class="qa-record-block"><span>可以这样讲</span>';
      html += renderStructuredNote(reply, "qa-record-points", "暂无整理出的回复口径。");
      html += "</div>";
    }
    html += '<div class="qa-record-block"><span>选项怎么判断</span>';
    html += renderQaOptionReasons(record, context) || '<p>暂无选项结构化说明。</p>';
    html += "</div>";
    if (bodyText) {
      html += '<details class="qa-raw-record"><summary>查看原始长记录</summary>';
      html += '<pre class="qa-detail-full">' + U.escapeHtml(bodyText) + "</pre>";
      html += "</details>";
    }
    html += "</div>";
    return html;
  }

  function renderQaIndexCard(state, record) {
    var eps = Store.getExamPointsForQa ? Store.getExamPointsForQa(state, record.id) : [];
    var primaryEp = eps[0];
    var context = getQaQuestionContext(state, record);
    var doubt = getQaStudentDoubt(record);
    var section = context.section || record.section || "";
    var sectionLabel = section && section !== "unknown" ? ("第 " + section + " 节") : "章节待核";
    var html = '<button class="qa-index-card" type="button" data-qa="' + U.escapeHtml(record.id || "") + '">';
    html += '<span class="qa-index-meta">';
    html += '<span class="qa-index-chip">' + U.escapeHtml(sectionLabel) + "</span>";
    if (context.id) html += '<span class="qa-index-chip">题 ' + U.escapeHtml(context.id) + "</span>";
    if (context.answer) html += '<span class="qa-index-chip">答案 ' + U.escapeHtml(context.answer) + "</span>";
    html += "</span>";
    html += '<strong class="qa-index-title">' + U.escapeHtml(U.shortText(doubt, 64)) + "</strong>";
    html += '<span class="qa-index-open">查看</span>';
    html += "</button>";
    return html;
  }

  function renderQaHistoryIndex(state) {
    var records = (state.qaRecords || []).slice().sort(function (a, b) {
      var sectionDiff = qaSectionSortKey(getQaDisplaySection(state, a)) - qaSectionSortKey(getQaDisplaySection(state, b));
      if (sectionDiff) return sectionDiff;
      return String(a.question || a.id).localeCompare(String(b.question || b.id), "zh-Hans-CN");
    });
    if (!records.length) {
      return '<div class="panel-section"><div class="panel-section-header">本章学生常问</div><div class="panel-section-body">' + empty("当前还没有导入学生答疑记录。") + "</div></div>";
    }

    var grouped = {};
    records.forEach(function (record) {
      var section = getQaDisplaySection(state, record);
      if (!grouped[section]) grouped[section] = [];
      grouped[section].push(record);
    });
    var sectionKeys = Object.keys(grouped).sort(function (a, b) {
      return qaSectionSortKey(a) - qaSectionSortKey(b);
    });

    var html = '<div class="panel-section qa-index-section"><div class="panel-section-header">本章学生常问 · ' + records.length + "</div>";
    html += '<div class="panel-section-body compact-body">';
    html += "</div>";

    sectionKeys.forEach(function (section) {
      var rows = grouped[section];
      html += '<div class="qa-index-group">';
      html += '<div class="qa-index-group-title">第 ' + U.escapeHtml(section) + ' 节<span>' + rows.length + " 条</span></div>";
      rows.slice(0, 3).forEach(function (record) {
        html += renderQaIndexCard(state, record);
      });
      if (rows.length > 3) {
        html += '<details class="qa-index-more"><summary>查看全部 ' + rows.length + " 条</summary>";
        rows.slice(3).forEach(function (record) {
          html += renderQaIndexCard(state, record);
        });
        html += "</details>";
      }
      html += "</div>";
    });
    html += "</div>";
    return html;
  }

  function renderWorkflowBox(mode, value) {
    var config = {
      explain: {
        title: "把新题贴进笔记",
        placeholder: "把题干和 A/B/C/D 选项粘贴在这里。笔记会先找相似题，再把答案判断、选项解析和教材证据摆出来。",
        action: "生成解析草稿"
      },
      qa: {
        title: "粘贴学生问题",
        placeholder: "把题干、选项和学生疑问粘贴在这里。",
        action: "生成答疑草稿"
      }
    }[mode];
    var html = '<div class="workflow-box">';
    html += '<label for="workflowInput">' + U.escapeHtml(config.title) + "</label>";
    if (mode === "explain") html += '<p class="workflow-hint">适合处理没有解析的官方新题。</p>';
    html += '<textarea id="workflowInput" rows="7" placeholder="' + U.escapeHtml(config.placeholder) + '">' + U.escapeHtml(value || "") + "</textarea>";
    html += '<div class="workflow-actions">';
    html += '<button class="action-button primary-action" type="button" data-workflow-run="' + U.escapeHtml(mode) + '">' + U.escapeHtml(config.action) + "</button>";
    html += "</div>";
    html += "</div>";
    return html;
  }

  function keywordTokens(text) {
    var source = String(text || "");
    var tokens = [];
    (source.match(/[\u4e00-\u9fa5]{2,}/g) || []).forEach(function (word) { tokens.push(word); });
    (source.match(/[A-Za-z][A-Za-z0-9_/.-]{1,}/g) || []).forEach(function (word) { tokens.push(word.toLowerCase()); });
    return U.unique(tokens)
      .slice(0, 16);
  }

  function scoreText(text, tokens) {
    var source = String(text || "");
    var lower = source.toLowerCase();
    return tokens.reduce(function (sum, token) {
      var needle = /[A-Za-z]/.test(token) ? token.toLowerCase() : token;
      var hay = /[A-Za-z]/.test(token) ? lower : source;
      return sum + (hay.indexOf(needle) >= 0 ? token.length : 0);
    }, 0);
  }

  function findTeachingEvidence(state, text) {
    var tokens = keywordTokens(text);
    var rows = [];
    if (!tokens.length) return rows;

    state.examPoints.forEach(function (ep) {
      var hay = [ep.title, ep.student_confusion, ep.reason, ep.type].concat((ep.source_card_details || []).map(function (card) {
        return [card.quote, card.knowledge, card.reason, card.chapter_path].join(" ");
      })).join(" ");
      var score = scoreText(hay, tokens);
      if (score > 0) rows.push({ type: "examPoint", score: score, ep: ep });
    });

    state.questions.forEach(function (question) {
      var mapping = Store.getOptionEvidenceForQuestion(state, question.id);
      var hay = [question.stem, question.explanation].concat((mapping && mapping.options || []).map(function (option) {
        return [option.option_text, option.explanation, option.common_trap].join(" ");
      })).join(" ");
      var score = scoreText(hay, tokens);
      if (score > 0) rows.push({ type: "question", score: score, question: question });
    });

    return rows.sort(function (a, b) { return b.score - a.score; }).slice(0, 5);
  }

  function renderMatchedQuestionDraft(state, question) {
    var mapping = Store.getOptionEvidenceForQuestion(state, question.id);
    var html = '<div class="draft-result">';
    html += '<div class="draft-block"><span>答案判断</span><strong>' + U.escapeHtml(question.answer || "待判断") + "</strong></div>";
    html += '<div class="draft-block"><span>题目</span><p>' + U.escapeHtml(question.stem || question.id) + "</p></div>";
    if (mapping && (mapping.options || []).length) {
      html += '<div class="draft-block"><span>教材证据来源</span>';
      var seenEvidence = {};
      (mapping.options || []).forEach(function (option) {
        var card = (option.evidence_cards || [])[0];
        if (!card) return;
        var quote = card.quote || card.citation || "";
        var key = (card.card_id || "") + "|" + quote;
        if (seenEvidence[key]) {
          seenEvidence[key].options.push(option.option || "");
          return;
        }
        seenEvidence[key] = {
          card: card,
          quote: quote,
          options: [option.option || ""]
        };
      });
      Object.keys(seenEvidence).slice(0, 4).forEach(function (key) {
        var row = seenEvidence[key];
        html += '<button class="compact-question-link" type="button" data-card="' + U.escapeHtml(row.card.card_id || "") + '">';
        html += '<strong>' + U.escapeHtml(row.options.join("/")) + renderPageLabelSuffix(state, row.card) + '</strong><span>' + U.escapeHtml(U.shortText(row.quote, 150)) + "</span>";
        html += "</button>";
      });
      html += "</div>";
      html += '<div class="draft-block"><span>选项解析草稿</span>';
      (mapping.options || []).forEach(function (option) {
      html += '<p><strong>' + U.escapeHtml(option.option || "") + ".</strong> " + U.escapeHtml(U.shortText(teacherText(option.explanation || option.option_text || ""), 170)) + "</p>";
      });
      html += "</div>";
    } else {
      html += '<div class="draft-block"><span>教材证据来源</span><p>这道题还没有整理到每个选项的教材依据，需要先补证后再定稿。</p></div>';
    }
    html += '<div class="panel-actions compact-actions"><button class="action-button" type="button" data-question="' + U.escapeHtml(question.id) + '">打开完整题目复核</button></div>';
    html += "</div>";
    return html;
  }

  function renderTeachingEvidenceResult(state, text) {
    var rows = findTeachingEvidence(state, text);
    var html = '<div class="draft-result">';
    if (!rows.length) {
      html += '<div class="draft-block"><span>教研依据</span><p>暂时没在本章里找到明显对应的教材原文。可以换关键词，或先人工补一条教材线索。</p></div>';
      html += "</div>";
      return html;
    }
    html += '<div class="draft-block"><span>教研依据</span>';
    rows.forEach(function (row) {
      if (row.type === "examPoint") {
        var ep = row.ep;
        var detail = (ep.source_card_details || [])[0] || {};
        html += '<button class="compact-question-link" type="button" data-exam-point="' + U.escapeHtml(ep.id || "") + '">';
        html += '<strong>' + U.escapeHtml(ep.title || "教材考点") + '</strong><span>' + U.escapeHtml(U.shortText(detail.quote || ep.student_confusion || ep.reason || "", 150)) + "</span>";
        html += "</button>";
      } else if (row.question) {
        html += '<button class="compact-question-link" type="button" data-question="' + U.escapeHtml(row.question.id || "") + '">';
        html += '<strong>相关题</strong><span>' + U.escapeHtml(U.shortText(row.question.stem || "", 150)) + "</span>";
        html += "</button>";
      }
    });
    html += "</div>";
    html += '<div class="draft-block"><span>给学生回复前先看</span><p>先确认上面的教材依据是否命中学生问题；确认后再整理成学生能看懂的一段话。</p></div>';
    html += "</div>";
    return html;
  }

  function formatRunSeconds(ms) {
    var value = Number(ms || 0);
    if (!value) return "0s";
    if (value < 1000) return Math.round(value) + "ms";
    return (value / 1000).toFixed(1) + "s";
  }

  function formatRunNumber(value) {
    value = Number(value || 0);
    if (!value) return "0";
    return value.toLocaleString ? value.toLocaleString("zh-CN") : String(value);
  }

  function renderNewQuestionRunInfo(draft) {
    return "";
  }

  function renderNewQuestionQuality(validate) {
    validate = validate || {};
    var checks = Array.isArray(validate.checks) ? validate.checks : [];
    var failed = checks.filter(function (check) {
      return String(check.status || "").toLowerCase() !== "pass";
    });
    if (!((validate.validation_status && validate.validation_status !== "passed") || failed.length)) {
      return "";
    }
    var first = failed[0] || {};
    var text = "";
    if (first.name === "question_type_answer_resolution") {
      text = "答案已生成；部分依据为相近教材表述，建议教研复核。";
    } else {
      text = "校验需复核：" + (first.detail || "有检查项未通过。");
    }
    return '<div class="draft-block draft-quality-summary"><span>质量校验</span><p>' + U.escapeHtml(text) + "</p></div>";
  }

  function getNewQuestionFailureMessage(draft) {
    var status = String((draft && draft.status) || "");
    if (!status || status === "draft") return "";
    var pipeline = (draft && draft.pipeline) || {};
    var retrieve = pipeline.retrieve_evidence || {};
    var final = (draft && draft.final) || {};
    var errorText = String(retrieve.error || final.overall_notes || "");
    if (/401|Authentication|api key|invalid_request_error/i.test(errorText)) {
      return "LLM 调用认证失败，通常是 DeepSeek API key 失效或云端环境变量未更新。";
    }
    if (/timeout|timed out/i.test(errorText)) {
      return "LLM 调用超时，稍后可以重试。";
    }
    var labels = {
      parse_failed: "题目解析失败，请检查粘贴内容是否包含完整题干和选项。",
      planner_failed: "搜索规划没有完成，AI 还没有进入证据检索和答案判断环节。",
      retrieval_failed: "教材证据检索失败，未能生成可用证据池。",
      adjudicator_failed: "答案判断没有完成，AI 未能生成可用解析。",
    };
    return labels[status] || "解析流程没有完成，请检查服务状态后重试。";
  }

  function renderNewQuestionFailure(draft) {
    var message = getNewQuestionFailureMessage(draft);
    if (!message) return "";
    return '<div class="workflow-error">' + U.escapeHtml(message) + "</div>";
  }

  function newQuestionJudgementLabel(judgement) {
    if (judgement === "correct") return "正确";
    if (judgement === "incorrect") return "排除";
    if (judgement === "partially_correct") return "部分支持";
    return "待复核";
  }

  function newQuestionJudgementClass(judgement) {
    if (judgement === "correct") return "is-correct";
    if (judgement === "incorrect") return "is-incorrect";
    return "is-review";
  }

  function summarizeNewQuestionOption(row) {
    if (row.display_summary) return cleanPipelineDisplayText(row.display_summary);
    if (row.explanation) return cleanPipelineDisplayText(row.explanation);
    var cards = Array.isArray(row.evidence_cards) ? row.evidence_cards : [];
    var quotes = cards
      .map(function (card) {
        return String(card.quote || card.reason || "").replace(/[。；;，,]\s*$/, "");
      })
      .filter(Boolean)
      .slice(0, 2);
    if (row.judgement === "correct" && quotes.length) {
      return "命中：" + quotes.join("；");
    }
    if (row.evidence_status === "conflict") return "教材依据与选项表述不一致。";
    if (row.evidence_status === "indirect") return "仅有间接相关原文，不足以支持该选项。";
    if (row.evidence_status === "none") return "未找到支持该选项的教材原文。";
    return cleanPipelineDisplayText(row.explanation || "暂无解析");
  }

  function renderNewQuestionOption(state, row) {
    var label = row.option || "";
    var judgement = row.judgement || "needs_manual";
    var cards = Array.isArray(row.evidence_cards) ? row.evidence_cards : [];
    var html = '<div class="draft-option-row ' + newQuestionJudgementClass(judgement) + '">';
    html += '<div class="draft-option-head"><strong>' + U.escapeHtml(label) + '</strong><b>' + U.escapeHtml(newQuestionJudgementLabel(judgement)) + "</b></div>";
    html += "<p>" + U.escapeHtml(summarizeNewQuestionOption(row)) + "</p>";
    cards.slice(0, 3).forEach(function (card, index) {
      html += '<button class="compact-question-link compact-evidence-link" type="button" data-card="' + U.escapeHtml(card.card_id || "") + '">';
      html += '<strong>教材原文 ' + U.escapeHtml(String(index + 1)) + renderPageLabelSuffix(state, card) + '</strong><span>' + U.escapeHtml(cleanPipelineDisplayText(card.quote || card.reason || "")) + "</span>";
      html += "</button>";
    });
    html += "</div>";
    return html;
  }

  function renderNewQuestionOverall(final) {
    var answer = (final.ai_answer || []).join("、") || "待判断";
    if (final.display_overall_notes) {
      return '<div class="draft-block draft-overall-summary"><span>整体说明</span><p>' + U.escapeHtml(cleanPipelineDisplayText(final.display_overall_notes)) + "</p></div>";
    }
    var rows = Array.isArray(final.display_option_explanations) ? final.display_option_explanations : (Array.isArray(final.option_explanations) ? final.option_explanations : []);
    var correct = rows.filter(function (row) { return row.judgement === "correct"; }).map(function (row) { return row.option; }).filter(Boolean);
    var excluded = rows.filter(function (row) { return row.judgement === "incorrect"; }).map(function (row) { return row.option; }).filter(Boolean);
    var text = "答案为 " + answer + "。";
    if (correct.length) text += " 正确项：" + correct.join("、") + "。";
    if (excluded.length) text += " 排除项：" + excluded.join("、") + "。";
    if (final.needs_teacher_review) text += " 系统提示仍需教研复核。";
    return '<div class="draft-block draft-overall-summary"><span>整体说明</span><p>' + U.escapeHtml(text) + "</p></div>";
  }

  function renderWorkflowErrorHint(workflowState, localHint) {
    var code = String((workflowState && workflowState.errorCode) || "");
    var error = String((workflowState && workflowState.error) || "");
    if (code === "server_busy_low_memory" || /可用内存不足|server_busy_low_memory/i.test(error)) {
      return '<p class="reference-note">云端内存正在恢复中，稍后重试即可；如果连续出现，说明当前服务器规格偏紧。</p>';
    }
    return '<p class="reference-note">' + U.escapeHtml(localHint) + "</p>";
  }

  function formatDraftTime(value) {
    if (!value) return "时间未知";
    var date = new Date(value);
    if (isNaN(date.getTime())) return String(value).replace("T", " ").slice(0, 16);
    function pad(num) {
      return String(num).padStart ? String(num).padStart(2, "0") : (num < 10 ? "0" + num : String(num));
    }
    return pad(date.getMonth() + 1) + "-" + pad(date.getDate()) + " " + pad(date.getHours()) + ":" + pad(date.getMinutes());
  }

  function renderNewQuestionDraftHistory(workflowState) {
    workflowState = workflowState || {};
    var drafts = Array.isArray(workflowState.drafts) ? workflowState.drafts : [];
    var html = '<div class="panel-section draft-history-section"><div class="panel-section-header">历史草稿';
    html += '<span class="draft-history-actions">';
    html += '<button class="text-mini-button" type="button" data-toggle-new-question-drafts>' + U.escapeHtml(workflowState.historyCollapsed ? "展开" : "收起") + "</button>";
    html += '<button class="text-mini-button" type="button" data-refresh-new-question-drafts>刷新</button>';
    html += "</span>";
    html += "</div>";
    if (workflowState.historyCollapsed) {
      html += '<div class="panel-section-body"><p class="reference-note">已收起 ' + U.escapeHtml(String(drafts.length)) + ' 条历史草稿。</p></div></div>';
      return html;
    }
    if (workflowState.draftsLoading) {
      html += '<div class="panel-section-body"><p class="reference-note">正在读取历史草稿。</p></div></div>';
      return html;
    }
    if (workflowState.draftsError) {
      html += '<div class="panel-section-body"><p class="reference-note">' + U.escapeHtml(workflowState.draftsError) + "</p></div></div>";
      return html;
    }
    if (!drafts.length) {
      html += '<div class="panel-section-body"><p class="reference-note">还没有保存过新题解析草稿。</p></div></div>';
      return html;
    }
    html += '<div class="draft-history-list">';
    drafts.slice(0, 8).forEach(function (draft) {
      var answer = Array.isArray(draft.ai_answer) ? draft.ai_answer.join(", ") : (draft.ai_answer || "待判断");
      var id = draft.draft_id || "";
      var active = workflowState.draft && workflowState.draft.draft_id === id;
      var loading = workflowState.historyLoadingId === id;
      var deleting = workflowState.deletingDraftId === id;
      html += '<div class="draft-history-row' + (active ? " active" : "") + '">';
      html += '<button class="draft-history-item" type="button" data-new-question-draft="' + U.escapeHtml(id) + '">';
      html += '<strong>' + U.escapeHtml(formatDraftTime(draft.created_at)) + '</strong>';
      html += '<span>答案 ' + U.escapeHtml(answer || "待判断") + "</span>";
      if (loading) html += "<em>读取中</em>";
      html += "</button>";
      html += '<button class="draft-delete-button" type="button" data-delete-new-question-draft="' + U.escapeHtml(id) + '" title="删除草稿" aria-label="删除草稿"' + (deleting ? " disabled" : "") + ">" + U.escapeHtml(deleting ? "..." : "删") + "</button>";
      html += "</div>";
    });
    html += "</div></div>";
    return html;
  }

  function renderStudentQaDraftHistory(workflowState) {
    workflowState = workflowState || {};
    var drafts = Array.isArray(workflowState.drafts) ? workflowState.drafts : [];
    var html = '<div class="panel-section draft-history-section"><div class="panel-section-header">历史答疑';
    html += '<span class="draft-history-actions">';
    html += '<button class="text-mini-button" type="button" data-toggle-student-qa-drafts>' + U.escapeHtml(workflowState.historyCollapsed ? "展开" : "收起") + "</button>";
    html += '<button class="text-mini-button" type="button" data-refresh-student-qa-drafts>刷新</button>';
    html += "</span>";
    html += "</div>";
    if (workflowState.historyCollapsed) {
      html += '<div class="panel-section-body"><p class="reference-note">已收起 ' + U.escapeHtml(String(drafts.length)) + ' 条历史答疑。</p></div></div>';
      return html;
    }
    if (workflowState.draftsLoading) {
      html += '<div class="panel-section-body"><p class="reference-note">正在读取历史答疑。</p></div></div>';
      return html;
    }
    if (workflowState.draftsError) {
      html += '<div class="panel-section-body"><p class="reference-note">' + U.escapeHtml(workflowState.draftsError) + "</p></div></div>";
      return html;
    }
    if (!drafts.length) {
      html += '<div class="panel-section-body"><p class="reference-note">还没有保存过学生答疑草稿。</p></div></div>';
      return html;
    }
    html += '<div class="draft-history-list">';
    drafts.slice(0, 8).forEach(function (draft) {
      var id = draft.draft_id || "";
      var active = workflowState.draft && workflowState.draft.draft_id === id;
      var loading = workflowState.historyLoadingId === id;
      var deleting = workflowState.deletingDraftId === id;
      var title = cleanPipelineDisplayText(draft.student_stuck_point || (draft.status === "failed" ? "运行失败" : "学生答疑草稿"));
      html += '<div class="draft-history-row' + (active ? " active" : "") + '">';
      html += '<button class="draft-history-item" type="button" data-student-qa-draft="' + U.escapeHtml(id) + '">';
      html += '<strong>' + U.escapeHtml(formatDraftTime(draft.created_at)) + '</strong>';
      html += '<span>' + U.escapeHtml(U.shortText(title, 30)) + "</span>";
      if (loading) html += "<em>读取中</em>";
      html += "</button>";
      html += '<button class="draft-delete-button" type="button" data-delete-student-qa-draft="' + U.escapeHtml(id) + '" title="删除答疑" aria-label="删除答疑"' + (deleting ? " disabled" : "") + ">" + U.escapeHtml(deleting ? "..." : "删") + "</button>";
      html += "</div>";
    });
    html += "</div></div>";
    return html;
  }

  function renderNewQuestionDraftResult(state, workflowState) {
    workflowState = workflowState || {};
    var html = '<div class="panel-section workflow-result"><div class="panel-section-header">解析草稿与教材依据</div><div class="panel-section-body">';
    if (workflowState.loading) {
      html += '<div class="workflow-status">正在运行解析，首次启动会加载教材证据池，请稍等。</div>';
      html += "</div></div>";
      return html;
    }
    if (workflowState.error) {
      html += '<div class="workflow-error">' + U.escapeHtml(workflowState.error) + "</div>";
      html += renderWorkflowErrorHint(workflowState, "请确认本地服务已启动：在“新题解析模块”目录运行 api/server.py。");
      html += "</div></div>";
      return html;
    }
    var draft = workflowState.draft;
    if (!draft) {
      html += '<p class="reference-note">粘贴新题后，会调用四角色盲判流程生成 AI 参考答案、选项解析和教材句卡依据。</p>';
      html += "</div></div>";
      return html;
    }

    var final = draft.final || {};
    var validate = (draft.pipeline || {}).validate || {};
    var answer = (final.ai_answer || []).join(", ") || "待判断";
    html += '<div class="draft-result">';
    html += '<div class="draft-block"><span>AI 参考答案</span><strong>' + U.escapeHtml(answer) + "</strong>";
    html += '<p>' + U.escapeHtml("置信度：" + confidenceLabel(final.confidence)) + "</p></div>";
    var examDirection = cleanPipelineDisplayText(final.exam_direction || final.exam_core_sentence || "");
    if (examDirection) {
      html += '<div class="draft-block"><span>题目考查方向</span><p>' + U.escapeHtml(examDirection) + "</p></div>";
    }
    html += renderNewQuestionRunInfo(draft);
    var failureHtml = renderNewQuestionFailure(draft);
    if (failureHtml) {
      html += failureHtml;
      html += "</div></div></div>";
      return html;
    }
    html += renderNewQuestionQuality(validate);

    var optionRows = Array.isArray(final.display_option_explanations) ? final.display_option_explanations : (final.option_explanations || []);
    if (optionRows.length) {
      html += '<div class="draft-block draft-option-list"><span>选项解析</span>';
      optionRows.forEach(function (row) {
      html += renderNewQuestionOption(state, row);
      });
      html += "</div>";
    }
    html += renderNewQuestionOverall(final);
    html += "</div></div></div>";
    return html;
  }

  function renderStudentQaDraftResult(state, workflowState) {
    workflowState = workflowState || {};
    var html = '<div class="panel-section workflow-result"><div class="panel-section-header">答疑草稿</div><div class="panel-section-body">';
    if (workflowState.loading) {
      html += '<div class="workflow-status">正在运行答疑，首次启动会加载教材证据池，请稍等。</div>';
      html += "</div></div>";
      return html;
    }
    if (workflowState.error) {
      html += '<div class="workflow-error">' + U.escapeHtml(workflowState.error) + "</div>";
      html += renderWorkflowErrorHint(workflowState, "请确认本地服务已启动：在“学生答疑模块_agentic”目录运行 api/server.py。");
      html += "</div></div>";
      return html;
    }
    var draft = workflowState.draft;
    if (!draft) {
      html += '<p class="reference-note">基于教材原文生成可复核答疑草稿。</p>';
      html += "</div></div>";
      return html;
    }

    var final = draft.final || {};
    var defaultEvidenceCards = Array.isArray(final.evidence_cards) ? final.evidence_cards : [];
    var allEvidenceCards = Array.isArray(final.evidence_cards_all) && final.evidence_cards_all.length
      ? final.evidence_cards_all
      : defaultEvidenceCards;
    var evidenceCards = workflowState.evidenceExpanded ? allEvidenceCards : defaultEvidenceCards;
    html += '<div class="draft-result">';
    html += '<div class="draft-block"><span>学生卡点</span><p>' + U.escapeHtml(cleanPipelineDisplayText(final.student_stuck_point || "暂未识别")) + "</p></div>";
    html += '<div class="draft-block draft-overall-summary"><span>可回复学生</span><p>' + U.escapeHtml(cleanPipelineDisplayText(final.reply_to_student || "暂未生成可用回复")) + "</p></div>";
    html += '<div class="draft-run-line">';
    html += "<em>" + U.escapeHtml("置信度：" + confidenceLabel(final.confidence)) + "</em>";
    if (final.needs_teacher_review) {
      html += "<em>建议教研复核</em>";
    }
    html += "</div>";
    if (final.review_reason) {
      html += '<div class="workflow-error">' + U.escapeHtml(cleanPipelineDisplayText(final.review_reason)) + "</div>";
    }
    if (evidenceCards.length) {
      html += '<div class="draft-block qa-evidence-compact"><span>依据原文</span>';
      evidenceCards.forEach(function (card, index) {
        var pageLabel = getCardPageLabel(state, card);
        html += '<button class="qa-evidence-line" type="button" data-card="' + U.escapeHtml(card.card_id || "") + '">';
        html += '<strong class="qa-evidence-ref"><span class="qa-evidence-title">' + U.escapeHtml("原文 " + (index + 1)) + "</span>";
        if (pageLabel) {
          html += '<span class="qa-evidence-page">' + U.escapeHtml(pageLabel) + "</span>";
        }
        html += '</strong><span class="qa-evidence-quote">' + U.escapeHtml(card.quote || "") + "</span>";
        html += "</button>";
      });
      if (allEvidenceCards.length > defaultEvidenceCards.length) {
        html += '<button class="text-mini-button qa-evidence-toggle" type="button" data-toggle-student-qa-evidence>';
        html += U.escapeHtml(workflowState.evidenceExpanded ? "收起依据" : ("显示更多依据（共 " + allEvidenceCards.length + " 条）"));
        html += "</button>";
      }
      html += "</div>";
    }
    var teacherTips = buildTeacherTips(final);
    if (teacherTips.length) {
      html += '<div class="draft-block qa-teacher-tips"><span>教研提示</span>';
      teacherTips.forEach(function (tip) {
        html += '<p>' + U.escapeHtml(tip) + "</p>";
      });
      html += "</div>";
    }
    html += "</div></div></div>";
    return html;
  }

  function cleanPipelineDisplayText(text) {
    return teacherText(text)
      .replace(/(?:原文)?教材原文(?:教材原文|原文)+/g, "教材原文")
      .replace(/原文教材原文/g, "教材原文")
      .replace(/\bC\d+\s*[：:、，,]?\s*/g, "")
      .replace(/\bclaim\s*\d*\s*[：:、，,]?\s*/gi, "")
      .replace(/\b(verdict|direct|indirect|none|conflict|needs_review)\b/gi, "")
      .replace(/^中关于/g, "关于")
      .replace(/\s{2,}/g, " ")
      .trim();
  }

  function buildTeacherTips(final) {
    final = final || {};
    var source = cleanPipelineDisplayText(final.teacher_notes || final.review_reason || "");
    source = source
      .replace(/有直接定义证据/g, "教材原文能直接支撑概念定义")
      .replace(/直接证据/g, "教材原文")
      .replace(/间接证据/g, "相近教材依据")
      .replace(/无证据/g, "暂未找到直接原文")
      .replace(/答疑草稿/g, "这份草稿");
    var parts = source
      .split(/[。；;]\s*/)
      .map(function (item) { return item.trim(); })
      .map(function (item) { return item.replace(/^中关于/, "关于"); })
      .filter(Boolean)
      .filter(function (item) {
        return !/\b(?:claim|verdict|usable|unsupported)\b/i.test(item);
      })
      .slice(0, 3);
    if (!parts.length && final.needs_teacher_review) {
      parts.push("这份草稿建议教研复核后再交付学生。");
    }
    if (!parts.length && final.confidence) {
      parts.push("这份草稿可作为教研初稿，建议结合教材原文快速核对。");
    }
    return parts.map(function (item) {
      return /[。！？]$/.test(item) ? item : item + "。";
    });
  }

  function renderWorkflowResult(state, mode, text, workflowState) {
    if (mode === "explain") return renderNewQuestionDraftResult(state, workflowState);
    if (mode === "qa" && workflowState && (workflowState.loading || workflowState.error || workflowState.draft)) {
      return renderStudentQaDraftResult(state, workflowState);
    }
    var normalized = String(text || "").trim();
    if (!normalized) return "";
    var matched = state.questions.find(function (question) {
      return normalized.indexOf(question.id) >= 0 ||
        (question.stem && normalized.indexOf(question.stem.slice(0, Math.min(18, question.stem.length))) >= 0);
    });
    var html = '<div class="panel-section workflow-result"><div class="panel-section-header">' + U.escapeHtml(mode === "qa" ? "教材依据与回复线索" : "解析草稿与教材依据") + '</div><div class="panel-section-body">';
    if (matched) {
      html += '<p class="reference-note">已匹配到题库里的同类题，下面是可复核的答案、解析和教材依据。</p>';
      html += renderMatchedQuestionDraft(state, matched);
    } else if (mode === "qa") {
      html += '<p class="reference-note">先按学生问题在本章里找教材依据和相近题目。</p>';
      html += renderTeachingEvidenceResult(state, normalized);
    } else {
      html += '<p class="reference-note">没有匹配到现有题。下面先列出可作为解析依据的教材线索。</p>';
      html += renderTeachingEvidenceResult(state, normalized);
    }
    html += "</div></div>";
    return html;
  }

  function renderWorkbenchHome(state, handlers, mode, workflowText, visibleNotes, workflowState) {
    var pane = getPane();
    if (!pane) return;
    mode = mode || "read";
    var trapEps = state.examPoints.filter(function (ep) { return getExamPointPriority(ep) === "trap"; });
    var linkedEps = state.examPoints.filter(function (ep) { return getExamPointPriority(ep) === "linked"; });
    var questionLinkedEps = state.examPoints.filter(function (ep) { return (ep.question_ids || []).length || (ep.option_bindings || []).length; });
    var withEvidence = state.questions.filter(function (q) { return getQuestionProfile(state, q).hasEvidence; });
    var withoutEvidence = state.questions.filter(function (q) { return !getQuestionProfile(state, q).hasEvidence; });
    var issueQuestions = state.questions.filter(function (q) {
      var profile = getQuestionProfile(state, q);
      return profile.hasIssues || profile.hasNoneEvidence;
    });

    var html = '<div class="panel-scroll">';
    html += '<div class="panel-head"><div class="panel-card-head">';
    html += '<div class="panel-meta"><span class="mode-label">' + U.escapeHtml(mode === "explain" ? "新题解析" : (mode === "qa" ? "学生答疑" : "看书备课")) + "</span>" + pill("教研笔记", "blue") + "</div>";
    if (mode !== "read") {
      html += '<h2 class="panel-title">' + U.escapeHtml(mode === "explain" ? "新题先入笔记，再复核原文。" : "基于教材原文生成可复核答疑草稿。") + "</h2>";
    }
    html += "</div></div>";
    html += '<div class="panel-body">';

    if (mode === "explain" || mode === "qa") {
      html += renderWorkflowBox(mode, workflowText);
      if (mode === "explain") html += renderNewQuestionDraftHistory(workflowState);
      if (mode === "qa") html += renderStudentQaDraftHistory(workflowState);
      html += renderWorkflowResult(state, mode, workflowText, workflowState);
    }

    if (mode === "read") {
      var currentNotes = visibleNotes || [];
      html += '<div class="panel-section handbook-section' + (currentNotes.length ? "" : " bare-handbook-section") + '">';
      if (currentNotes.length) {
        currentNotes.forEach(function (note) { html += renderVisibleNote(note); });
      }

      html += '<div class="panel-section-body handbook-actions-body"><div class="panel-actions handbook-actions">';
      html += '<button class="action-button" type="button" data-home-action="exam-points" data-exam-filter="priority">高频考点</button>';
      html += '<button class="action-button" type="button" data-home-action="questions" data-question-filter="traps">易错相关</button>';
      html += "</div></div></div>";
    }

    if (mode === "qa" && !workflowText) {
      html += renderQaHistoryIndex(state);
    }

    if (mode === "read") {
      html += '<div class="panel-section"><div class="panel-section-header">本章概览</div><div class="panel-section-body">';
      if (trapEps.length) {
        html += '<p class="coverage-line"><strong>' + questionLinkedEps.length + '</strong> 个考点已经和题目/答疑连上，<strong>' + trapEps.length + "</strong> 个有易错提醒。</p>";
      } else {
        html += '<p class="coverage-line"><strong>' + questionLinkedEps.length + "</strong> 个考点已经和题目/答疑连上，可在考点详情里核对教材依据。</p>";
      }
      html += '<p class="coverage-line"><strong>' + withEvidence.length + '</strong> 道题已有教材依据，<strong>' + withoutEvidence.length + "</strong> 道题还需要补解析。</p>";
      html += "</div></div>";
    }
    html += "</div></div>";

    pane.innerHTML = html;
    bindBackEvent(pane, handlers);
    bindSharedPanelEvents(pane, handlers);
    bindFilterEvents(pane, handlers);
    bindWorkflowEvents(pane, handlers);
  }

  function renderConceptTree(concept, selectedTarget) {
    var html = '<div class="graph-tree">';
    html += '<div class="tree-current"><p class="tree-current-title">' + U.escapeHtml(concept.name) + "</p></div>";
    if (concept.edges.length) {
      html += '<div class="tree-children">';
      concept.edges.slice(0, 8).forEach(function (edge) {
        var active = selectedTarget === edge.target;
        html += '<button class="tree-node' + (active ? " active" : "") + '" type="button" data-edge-target="' + U.escapeHtml(edge.target) + '">';
        html += '<span class="tree-edge">' + U.escapeHtml(edge.type || "关系") + "</span>";
        html += '<span class="tree-node-title">' + U.escapeHtml(edge.target) + "</span>";
        html += "</button>";
      });
      html += "</div>";
    } else {
      html += '<div class="tree-empty">当前概念暂无跨节点关系。</div>';
    }
    html += "</div>";
    return html;
  }

  function renderConceptBody(state, card, selectedTarget) {
    var concept = Store.getCardSection(state, card.card_id);
    if (!concept) {
      return '<div class="panel-body"><div class="panel-section"><div class="panel-section-header">原文位置</div>' +
        empty("这段原文暂时没有整理出上下游关系。") + "</div></div>";
    }

    var info = concept.info || {};
    var selectedEdge = concept.edges.find(function (edge) {
      return edge.target === selectedTarget;
    }) || concept.edges[0] || null;

    var html = '<div class="panel-body panel-body-compact">';
    html += '<details class="panel-section density-section">';
    html += '<summary class="panel-section-header">相关知识关系</summary>';
    html += '<div class="panel-section">';
    html += '<div class="panel-section-header">当前知识点</div>';
    html += '<div class="panel-section-body">';
    html += '<h3 class="concept-title">' + U.escapeHtml(concept.name) + "</h3>";
    html += '<p class="concept-definition">' + U.escapeHtml(info.definition || "暂无定义") + "</p>";
    html += '<div class="panel-actions">';
    html += '<button class="action-button" type="button" data-action="locate-current">查看原文</button>';
    if (concept.edges.length) {
      html += '<button class="action-button" type="button" data-action="open-modal">放大图谱</button>';
    }
    html += "</div></div></div>";

    if (concept.edges.length) {
      html += '<div class="panel-section">';
      html += '<div class="panel-section-header">关系树</div>';
      html += '<div class="panel-section-body">' + renderConceptTree(concept, selectedEdge && selectedEdge.target) + "</div>";
      html += "</div>";
    }

    if (selectedEdge) {
      var targetCard = Store.getBestCardForSection(state, selectedEdge.target);
      html += '<div class="detail-box">';
      html += '<h4>' + U.escapeHtml(selectedEdge.type || "关系") + "： " + U.escapeHtml(concept.name) + " → " + U.escapeHtml(selectedEdge.target) + "</h4>";
      html += '<p>' + U.escapeHtml(selectedEdge.detail || "暂无关系说明。") + "</p>";
      html += '<div class="panel-actions">';
      html += '<button class="action-button" type="button" data-action="switch-section" data-section="' + U.escapeHtml(selectedEdge.target) + '">查看这个概念</button>';
      if (targetCard) {
        html += '<button class="action-button" type="button" data-action="locate-target" data-card="' + U.escapeHtml(targetCard) + '">查看目标原文</button>';
      }
      html += "</div></div>";
    }

    html += "</details></div>";
    return html;
  }

  function getExamPointSourceDetails(ep) {
    var byId = {};
    (ep.source_card_details || []).forEach(function (detail) {
      var cid = detail.card_id || detail.id;
      if (cid) byId[cid] = detail;
    });
    return byId;
  }

  function getExamPointExternalDetails(ep) {
    var byId = {};
    (ep.external_source_card_details || []).forEach(function (detail) {
      var cid = detail.card_id || detail.id;
      if (cid) byId[cid] = detail;
    });
    return byId;
  }

  function buildExamPointEvidenceCards(state, ep, cardIds, includeAllDetails) {
    var detailById = getExamPointSourceDetails(ep);
    var ids = includeAllDetails ? U.unique((cardIds || []).concat(Object.keys(detailById))) : U.unique(cardIds || []);
    return ids.map(function (cid) {
      var detail = detailById[cid] || {};
      var card = state.cardById[cid] || {};
      return {
        card_id: cid,
        support_type: detail.support_type || card.support_type || "",
        relevance: detail.relevance || card.relevance || "",
        quote: detail.quote || detail.citation || card.citation || "",
        knowledge: detail.knowledge || card.knowledge || "",
        reason: detail.reason || "",
        chapter_path: detail.chapter_path || state.cardToSection[cid] || "",
        source_line_start: detail.source_line_start || card.source_line_start || "",
        canLocate: !!state.cardById[cid]
      };
    }).filter(function (card) {
      return !!card.card_id;
    });
  }

  function buildExamPointExternalEvidenceCards(state, ep) {
    var detailById = getExamPointExternalDetails(ep);
    var ids = U.unique((ep.external_source_card_ids || []).concat(Object.keys(detailById)));
    return ids.map(function (cid) {
      var detail = detailById[cid] || {};
      return {
        card_id: cid,
        support_type: detail.support_type || "",
        relevance: detail.relevance || "",
        quote: detail.quote || detail.citation || "",
        knowledge: detail.knowledge || "",
        reason: detail.reason || "",
        chapter_path: detail.chapter_path || "",
        source_line_start: detail.source_line_start || "",
        canLocate: !!state.cardById[cid]
      };
    }).filter(function (card) {
      return !!card.card_id;
    });
  }

  function renderEvidenceCards(state, cards, options) {
    options = options || {};
    var isNotebook = options.variant === "notebook";
    var compact = options.variant === "compact";
    var plainQuotes = options.variant === "plainQuotes";
    var labelPrefix = options.labelPrefix || (isNotebook ? "当前页原文 " : compact ? "补充依据 " : "教材原文 ");
    var html = '<div class="option-evidence-cards' + (isNotebook ? " evidence-cards-notebook" : "") + (plainQuotes ? " evidence-cards-plain" : "") + '">';
    cards.forEach(function (card, index) {
      var pageLabel = getCardPageLabel(state, card);
      var hint = [];
      if (card.knowledge) hint.push("知识点：" + card.knowledge);
      if (card.reason) hint.push("引用理由：" + card.reason);
      var title = !plainQuotes && hint.length ? ' title="' + U.escapeHtml(hint.join("\n")) + '"' : "";
      html += '<button class="evidence-card' + (plainQuotes ? " evidence-card-plain" : "") + (card.canLocate ? "" : " candidate-only") + '" type="button" data-card="' + U.escapeHtml(card.card_id) + '"' + title + '>';
      if (plainQuotes) {
        html += '<span class="evidence-plain-index">' + (index + 1) + (pageLabel ? " · " + U.escapeHtml(pageLabel) : "") + "</span>";
        html += '<span class="evidence-plain-quote">' + U.escapeHtml(card.quote || "暂未摘录原文。") + "</span>";
        html += "</button>";
        return;
      }
      html += '<span class="evidence-card-top">';
      html += '<span class="evidence-card-id">' + U.escapeHtml(labelPrefix) + (index + 1) + (pageLabel ? " · " + U.escapeHtml(pageLabel) : "") + "</span>";
      if (!isNotebook && !compact) {
        if (card.support_type) html += '<span class="evidence-pill support-' + U.escapeHtml(card.support_type) + '">' + U.escapeHtml(supportTypeLabel(card.support_type)) + "</span>";
        if (card.relevance) html += '<span class="evidence-pill">' + U.escapeHtml(confidenceLabel(card.relevance)) + "</span>";
      }
      html += "</span>";
      if (!isNotebook && card.knowledge) {
        html += '<span class="evidence-reason"><strong>知识点</strong>：' + U.escapeHtml(card.knowledge) + "</span>";
      }
      if (card.quote || isNotebook) {
        html += '<span class="evidence-quote">' + U.escapeHtml(card.quote || "暂未摘录原文。") + "</span>";
      }
      if (!isNotebook && !compact && card.reason) {
        html += '<span class="evidence-reason"><strong>匹配理由</strong>：' + U.escapeHtml(card.reason) + "</span>";
      }
      if (!compact && (card.chapter_path || card.source_line_start || pageLabel)) {
        var origin = card.chapter_path || "未挂载";
        if (!pageLabel && !isNotebook && card.source_line_start) origin += " · line " + card.source_line_start;
        html += '<span class="evidence-origin">' + U.escapeHtml(origin) + "</span>";
      }
      html += "</button>";
    });
    html += "</div>";
    return html;
  }

  function renderExamPointSourceCards(state, ep) {
    var cards = buildExamPointEvidenceCards(state, ep, ep.source_card_ids || [], true);
    var externalCards = buildExamPointExternalEvidenceCards(state, ep);
    var html = '<div class="panel-section"><div class="panel-section-header">教材依据 · ' + (cards.length + externalCards.length) + "</div>";
    if (!cards.length && !externalCards.length) {
      html += '<div class="panel-section-body">' + empty("这个考点暂时没有可引用的教材依据。") + "</div>";
    } else {
      html += renderEvidenceCards(state, cards.concat(externalCards), { variant: "plainQuotes" });
    }
    html += "</div>";
    return html;
  }

  function renderExamPointOptionBindings(state, ep) {
    var bindings = ep.option_bindings || [];
    if (!bindings.length) return "";
    var html = '<div class="panel-section"><div class="panel-section-header">相关题目选项 · ' + bindings.length + "</div>";
    html += '<div class="panel-section-body compact-body"><p class="reference-note">这些选项说明这个考点通常怎么考，可辅助判断“题目、选项、解析、教材原文”是否闭环。</p></div>';
    bindings.forEach(function (binding) {
      var status = binding.evidence_status || "none";
      var question = state.questionById[binding.question_id] || {};
      var evidenceCards = buildExamPointEvidenceCards(state, ep, binding.evidence_card_ids || [], false);
      html += '<div class="option-evidence-row status-' + U.escapeHtml(status) + '">';
      html += '<div class="option-evidence-head">';
      html += '<div class="option-evidence-key">' + U.escapeHtml(binding.option || "") + "</div>";
      html += '<div class="option-evidence-title">';
      html += '<p>' + U.escapeHtml(binding.option_text || "") + "</p>";
      html += '<div class="option-evidence-meta">';
      html += '<span class="evidence-pill">' + U.escapeHtml(binding.question_id || "未绑定题目") + "</span>";
      html += '<span class="evidence-pill status-' + U.escapeHtml(status) + '">' + U.escapeHtml(evidenceStatusLabel(status)) + "</span>";
      html += '<span class="evidence-pill">' + U.escapeHtml(judgementLabel(binding.judgement)) + "</span>";
      if (binding.needs_teacher_review) html += '<span class="evidence-pill review">教研复核</span>';
      html += "</div></div></div>";
      if (question.stem) {
        html += '<div class="option-analysis"><strong>题干</strong><p>' + U.escapeHtml(U.shortText(question.stem, 180)) + "</p></div>";
      }
      if (evidenceCards.length) {
        html += renderEvidenceCards(state, evidenceCards);
      } else {
        html += '<div class="option-evidence-empty">该选项暂时没有可引用的教材原文。</div>';
      }
      if (binding.explanation) {
        html += '<div class="option-analysis"><strong>解析</strong><p>' + U.escapeHtml(teacherText(binding.explanation)) + "</p></div>";
      }
      if (binding.common_trap) {
        html += '<div class="option-trap"><strong>易错点</strong><p>' + U.escapeHtml(binding.common_trap) + "</p></div>";
      }
      if (binding.teacher_review_reason) {
        html += '<div class="option-review-note">' + U.escapeHtml(binding.teacher_review_reason) + "</div>";
      }
      html += '<div class="option-evidence-actions"><button class="fb-button" type="button" data-question="' + U.escapeHtml(binding.question_id || "") + '">查看题目</button></div>';
      html += "</div>";
    });
    html += "</div>";
    return html;
  }

  function renderExamPointIssues(ep) {
    var issueCount = ((ep.source_data_issues || []).length) + ((ep.validation_issues || []).length);
    if (!issueCount) return "";
    var html = '<div class="panel-section"><div class="panel-section-header">数据/校验问题 · ' + issueCount + "</div>";
    html += '<div class="panel-section-body compact-body">';
    html += '<p class="reference-note">这些问题会影响考点、题目、选项和教材证据的闭环可信度，需要先修数据或人工复核。</p>';
    html += renderIssueList("源题数据问题", ep.source_data_issues);
    html += renderIssueList("校验问题", ep.validation_issues);
    html += "</div></div>";
    return html;
  }

  function renderExamPointQa(state, ep, options) {
    var records = Store.getQaForExamPoint(state, ep);
    var rawCount = (ep.qa_ids || []).length;
    if (options && options.hideWhenEmpty && !rawCount) return "";
    var html = '<div class="panel-section"><div class="panel-section-header">关联答疑 · ' + rawCount + "</div>";
    if (!rawCount) {
      html += '<div class="panel-section-body">' + empty("这个考点暂时没有学生答疑。") + "</div>";
    } else if (!records.length) {
      html += '<div class="panel-section-body"><p class="reference-note">有答疑 ID，但当前答疑数据中未能匹配到完整记录。</p></div>';
    } else {
      records.slice(0, 3).forEach(function (record) {
        var context = getQaQuestionContext(state, record);
        var doubt = getQaStudentDoubt(record);
        html += '<button class="qa-card" type="button" data-qa="' + U.escapeHtml(record.id || "") + '">';
        html += '<span class="qa-label">学生常问</span>';
        html += '<p class="qa-title">' + U.escapeHtml(U.shortText(doubt, 120)) + "</p>";
        if (context.stem) html += '<p class="qa-meta">题目：' + U.escapeHtml(U.shortText(context.stem, 90)) + "</p>";
        html += '<span class="qa-open">查看答疑</span>';
        html += "</button>";
      });
      if (records.length > 3) {
        html += '<div class="panel-section-body"><p class="reference-note">另有 ' + (records.length - 3) + " 条答疑未展开。</p></div>";
      }
    }
    html += "</div>";
    return html;
  }

  function renderTeacherQuestionPreview(state, ep) {
    var questions = Store.getQuestionsForExamPoint(state, ep);
    if (!questions.length) {
      return '<div class="panel-section"><div class="panel-section-header">相关题目</div><div class="panel-section-body">' + empty("暂时没有关联题。") + "</div></div>";
    }
    var html = '<div class="panel-section"><div class="panel-section-header">相关题目 · ' + questions.length + "</div>";
    questions.slice(0, 3).forEach(function (question) {
      html += '<button class="teacher-question-preview" type="button" data-question="' + U.escapeHtml(question.id) + '">';
      html += '<span>题 ' + U.escapeHtml(question.id) + (question.answer ? " · 答案 " + U.escapeHtml(question.answer) : "") + "</span>";
      html += '<strong>' + U.escapeHtml(U.shortText(question.stem || "", 120)) + "</strong>";
      html += "</button>";
    });
    if (questions.length > 3) {
      html += '<div class="panel-section-body"><p class="reference-note">另有 ' + (questions.length - 3) + " 道题，点开题目后再逐题复核。</p></div>";
    }
    html += "</div>";
    return html;
  }

  function renderExamPointSummary(state, ep, options) {
    var compact = options && options.compact;
    var body = "";
    var html = "";
    body += '<h3 class="concept-title">' + U.escapeHtml(ep.title) + "</h3>";
    body += '<div class="ep-metrics">';
    body += '<span>题目 ' + ((ep.question_ids || []).length) + "</span>";
    body += '<span>答疑 ' + ((ep.qa_ids || []).length) + "</span>";
    body += renderExamPointEvidenceMeta(ep);
    body += "</div>";
    body += '<div class="ep-field"><div class="ep-field-label">类型</div><div class="ep-field-value">' + U.escapeHtml(ep.type || "待分类") + "</div></div>";
    if (ep.student_confusion) {
      body += '<div class="ep-field"><div class="ep-field-label">学生误区</div><div class="ep-field-value">' + U.escapeHtml(ep.student_confusion) + "</div></div>";
    }
    if (ep.reason && !compact) {
      body += '<div class="ep-field"><div class="ep-field-label">笔记整理说明</div><div class="ep-field-value">' + U.escapeHtml(teacherText(ep.reason).replace(/候选卡片/g, "教材线索")) + "</div></div>";
    }
    if (ep.teacher_note) {
      body += '<div class="ep-field"><div class="ep-field-label">教研备注</div><div class="ep-field-value">' + U.escapeHtml(ep.teacher_note) + "</div></div>";
    } else if (!compact) {
      body += '<div class="ep-field"><div class="ep-field-label">教研备注</div><div class="ep-field-value"><span class="placeholder-text">待补充教研备注</span></div></div>';
    }
    if (options && options.bare) return body;
    html = '<div class="panel-section-body">';
    html += body;
    html += "</div>";
    return html;
  }

  function renderExamPointConclusion(state, ep, options) {
    var questions = Store.getQuestionsForExamPoint(state, ep);
    var qa = Store.getQaForExamPoint(state, ep);
    var priority = getExamPointPriority(ep);
    var title = {
      trap: "易错提醒",
      linked: "关联题",
      review: "待补充依据",
      candidate: "基础知识点"
    }[priority] || "待判断";
    var lead = ep.student_confusion ||
      (/^needs_/.test(ep.status || "") ? "这个考点还需要补充依据或人工确认。" : "") ||
      "";
    if (priority === "trap" && ep.student_confusion) {
      lead = "这个考点容易混淆相近概念或误判适用场景，需要重点提醒。";
    }
    var html = '<div class="conclusion-card priority-' + U.escapeHtml(priority) + '">';
    html += '<div class="conclusion-head"><span>提醒类型</span><strong>' + U.escapeHtml(title) + "</strong></div>";
    if (lead) {
      html += renderStructuredNote(lead, "conclusion-points", "");
    }
    if (!(options && options.hideMetrics)) {
      html += '<div class="conclusion-metrics">';
      html += '<span>题目 <strong>' + questions.length + "</strong></span>";
      html += '<span>答疑 <strong>' + ((ep.qa_ids || []).length || qa.length) + "</strong></span>";
      html += renderExamPointEvidenceMeta(ep);
      html += "</div>";
    }
    if (!(options && options.hideActions)) {
      html += '<div class="panel-actions compact-actions">';
      if (questions[0]) {
        html += '<button class="action-button" type="button" data-question="' + U.escapeHtml(questions[0].id) + '">查看题目</button>';
      }
      html += '<button class="action-button" type="button" data-exam-point="' + U.escapeHtml(ep.id) + '">查看详情</button>';
      if (options && options.showReview) {
        html += '<button class="action-button" type="button" data-fb-action="confirmed" data-fb-ep="' + U.escapeHtml(ep.id) + '">确认考点</button>';
      }
      html += "</div>";
    }
    html += "</div>";
    return html;
  }

  function renderExamPointQuestionLinks(state, ep) {
    var questions = Store.getQuestionsForExamPoint(state, ep);
    if (!questions.length) return empty("这个考点暂时没有相关题。");
    var html = '<div class="compact-question-list">';
    questions.slice(0, 5).forEach(function (question) {
      html += '<button class="compact-question-link" type="button" data-question="' + U.escapeHtml(question.id) + '">';
      html += '<strong>' + U.escapeHtml(question.id) + '</strong><span>' + U.escapeHtml(U.shortText(question.stem || "", 120)) + "</span>";
      html += "</button>";
    });
    if (questions.length > 5) {
      html += '<p class="reference-note">另有 ' + (questions.length - 5) + " 道关联题未展开。</p>";
    }
    html += "</div>";
    return html;
  }

  function renderTeachingSnapshot(state, ep) {
    var questions = Store.getQuestionsForExamPoint(state, ep);
    var qa = Store.getQaForExamPoint(state, ep);
    var html = '<div class="teaching-snapshot">';
    html += '<span>关联题 <strong>' + questions.length + "</strong></span>";
    html += '<span>答疑 <strong>' + ((ep.qa_ids || []).length || qa.length) + "</strong></span>";
    html += renderExamPointEvidenceMeta(ep);
    html += "</div>";
    if (ep.student_confusion) {
      html += '<div class="teacher-warning"><strong>易错提醒</strong>' + renderStructuredNote(splitStructuredItems(ep.student_confusion, 3).join("。"), "teacher-warning-points", "") + "</div>";
    }
    return html;
  }

  function renderExamPointSection(state, cid) {
    var eps = Store.getExamPointsForCard(state, cid);
    if (!eps.length) return "";
    var html = "";
    eps.forEach(function (ep) {
      html += '<div class="panel-section">';
      html += '<div class="panel-section-header">考点</div>';
      html += '<div class="panel-section-body panel-section-body-tight">';
      html += '<div class="exam-point-brief">';
      html += '<p class="exam-point-brief-title">' + U.escapeHtml(ep.title || ep.id) + "</p>";
      html += '<p class="exam-point-brief-meta">' + U.escapeHtml(renderExamPointInlineMeta(state, ep)) + "</p>";
      html += '<div class="panel-actions compact-actions single-action">';
      html += '<button class="action-button" type="button" data-exam-point="' + U.escapeHtml(ep.id) + '">查看详情</button>';
      html += "</div>";
      html += "</div>";
      html += "</div></div>";
    });
    return html;
  }

  function bindSharedPanelEvents(pane, handlers) {
    pane.querySelectorAll("[data-question]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (handlers.selectQuestion) handlers.selectQuestion(button.getAttribute("data-question"));
      });
    });
    pane.querySelectorAll("[data-card]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (handlers.selectCard) handlers.selectCard(button.getAttribute("data-card"), { scroll: true });
      });
    });
    pane.querySelectorAll("[data-exam-point]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (handlers.selectExamPoint) handlers.selectExamPoint(button.getAttribute("data-exam-point"));
      });
    });
    pane.querySelectorAll("[data-qa]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (handlers.selectQa) handlers.selectQa(button.getAttribute("data-qa"));
      });
    });
    pane.querySelectorAll("[data-fb-action]").forEach(function (button) {
      button.addEventListener("click", function () {
        var action = button.getAttribute("data-fb-action");
        var epId = button.getAttribute("data-fb-ep");
        if (handlers.submitFeedback) handlers.submitFeedback(epId, action);
      });
    });
  }

  function bindOptionDetailEvents(pane, handlers) {
    pane.querySelectorAll("[data-option-detail]").forEach(function (details) {
      details.addEventListener("toggle", function () {
        if (!details.open || details.getAttribute("data-loaded") === "true") return;
        var body = details.querySelector(".option-detail-body");
        var payload = details.getAttribute("data-option-payload") || "";
        try {
          var parsed = JSON.parse(payload);
          if (body) body.innerHTML = parsed.html || "";
          details.setAttribute("data-loaded", "true");
          bindSharedPanelEvents(details, handlers);
          details.querySelectorAll("[data-option-fb-action]").forEach(function (button) {
            button.addEventListener("click", function () {
              if (!handlers.submitOptionFeedback) return;
              handlers.submitOptionFeedback(
                button.getAttribute("data-fb-question"),
                button.getAttribute("data-fb-option"),
                button.getAttribute("data-option-fb-action"),
                button.getAttribute("data-fb-card"),
                button.getAttribute("data-fb-status")
              );
            });
          });
        } catch (err) {
          if (body) body.innerHTML = '<div class="option-evidence-empty">证据详情加载失败，请刷新后重试。</div>';
        }
      });
    });
  }

  function renderExamPointDetail(state, epid, handlers, options) {
    var pane = getPane();
    var ep = Store.getExamPoint(state, epid);
    if (!pane || !ep) return;

    var html = '<div class="panel-scroll">';
    html += renderPanelHeadStart(options);
    html += '<div class="panel-meta"><span class="mode-label">教研笔记</span></div>';
    html += '<h2 class="panel-title">' + U.escapeHtml(ep.title || ep.id) + "</h2>";
    html += "</div></div>";
    html += '<div class="panel-body">';
    if (ep.student_confusion) {
      html += '<div class="panel-section teacher-brief-section"><div class="panel-section-header">易错提醒</div>';
      html += '<div class="panel-section-body panel-section-body-tight">';
      html += renderTeachingSnapshot(state, ep);
      html += "</div></div>";
    }
    html += renderExamPointSourceCards(state, ep);
    html += renderTeacherQuestionPreview(state, ep);
    html += renderExamPointQa(state, ep, { hideWhenEmpty: true });
    html += "</div></div>";

    pane.innerHTML = html;
    bindBackEvent(pane, handlers);
    bindSharedPanelEvents(pane, handlers);
    bindOptionDetailEvents(pane, handlers);
  }

  function renderExamPointList(state, handlers, activeFilter, options) {
    var pane = getPane();
    if (!pane) return;
    activeFilter = activeFilter || "priority";
    var rows = state.examPoints.filter(function (ep) {
      var priority = getExamPointPriority(ep);
      if (activeFilter === "priority") return priority !== "candidate";
      if (activeFilter === "trap") return priority === "trap";
      if (activeFilter === "linked") return (ep.question_ids || []).length || (ep.option_bindings || []).length;
      if (activeFilter === "review") return priority === "review";
      if (activeFilter === "candidate") return priority === "candidate";
      return true;
    });
    var priorityCount = state.examPoints.filter(function (ep) { return getExamPointPriority(ep) !== "candidate"; }).length;
    var trapCount = state.examPoints.filter(function (ep) { return getExamPointPriority(ep) === "trap"; }).length;
    var linkedCount = state.examPoints.filter(function (ep) { return (ep.question_ids || []).length || (ep.option_bindings || []).length; }).length;
    var reviewCount = state.examPoints.filter(function (ep) { return getExamPointPriority(ep) === "review"; }).length;
    var candidateCount = state.examPoints.filter(function (ep) { return getExamPointPriority(ep) === "candidate"; }).length;
    var filters = [
      { id: "priority", label: "重点考点", count: priorityCount },
      { id: "trap", label: "易错考点", count: trapCount },
      { id: "linked", label: "有题目", count: linkedCount },
      { id: "review", label: "缺依据", count: reviewCount },
      { id: "candidate", label: "基础考点", count: candidateCount },
      { id: "all", label: "全部", count: state.examPoints.length }
    ];
    var activeFilterInfo = filters.filter(function (item) { return item.id === activeFilter; })[0] || filters[0];

    var html = '<div class="panel-scroll">';
    html += renderPanelHeadStart(options);
    html += '<div class="panel-meta"><span class="mode-label">教材考点</span>' + pill(rows.length + " / " + state.examPoints.length + " 个", "blue") + "</div>";
    html += '<h2 class="panel-title">教材考点目录</h2>';
    html += '<p class="panel-citation">按易错、题目关联和教材依据筛选考点。</p>';
    html += renderFilterBar("exam", filters, activeFilter);
    html += "</div></div>";
    html += '<div class="panel-body">';

    if (rows.length) {
      html += '<div class="panel-section"><div class="panel-section-header">' + U.escapeHtml(activeFilterInfo.label) + " · " + rows.length + "</div>";
      rows.forEach(function (ep) { html += renderSmallExamPointCard(state, ep); });
      html += "</div>";
    } else {
      html += '<div class="panel-section"><div class="panel-section-body">' + empty("当前筛选下暂无考点。") + "</div></div>";
    }
    html += "</div></div>";

    pane.innerHTML = html;
    bindBackEvent(pane, handlers);
    bindSharedPanelEvents(pane, handlers);
    bindFilterEvents(pane, handlers);
  }

  function renderConcept(state, cid, selectedTarget, handlers, options) {
    var pane = getPane();
    var card = state.cardById[cid];
    if (!pane || !card) return;
    var concept = Store.getCardSection(state, cid);

    var html = '<div class="panel-scroll">';
    html += renderPanelHeadStart(options);
    html += '<div class="panel-meta"><span class="mode-label">原文依据</span>' + pill(concept ? concept.name : "教材原文", "blue") + "</div>";
    html += '<h2 class="panel-title">' + U.escapeHtml(card.knowledge || cid) + "</h2>";
    html += '<p class="panel-citation">' + U.escapeHtml(U.shortText(card.citation || "", 180)) + "</p>";
    html += "</div></div>";
    var examPointHtml = renderExamPointSection(state, cid);
    if (examPointHtml) {
      html += '<div class="panel-body panel-body-compact">' + examPointHtml + "</div>";
    }
    html += renderConceptBody(state, card, selectedTarget);
    html += "</div>";

    pane.innerHTML = html;
    bindBackEvent(pane, handlers);
    pane.querySelectorAll("[data-edge-target]").forEach(function (button) {
      button.addEventListener("click", function () {
        handlers.selectEdge(button.getAttribute("data-edge-target"));
      });
    });
    pane.querySelectorAll("[data-action]").forEach(function (button) {
      button.addEventListener("click", function () {
        var action = button.getAttribute("data-action");
        if (action === "locate-current") handlers.locateCard(cid);
        if (action === "open-modal") handlers.openGraphModal(cid);
        if (action === "switch-section") handlers.selectSection(button.getAttribute("data-section"), { scroll: false });
        if (action === "locate-target") handlers.selectCard(button.getAttribute("data-card"), { scroll: true });
      });
    });
    // Feedback buttons
    pane.querySelectorAll("[data-fb-action]").forEach(function (button) {
      button.addEventListener("click", function () {
        var action = button.getAttribute("data-fb-action");
        var epId = button.getAttribute("data-fb-ep");
        if (handlers.submitFeedback) handlers.submitFeedback(epId, action);
      });
    });
    // Question chips in exam point section
    pane.querySelectorAll("[data-question]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (handlers.selectQuestion) handlers.selectQuestion(button.getAttribute("data-question"));
      });
    });
    // Exam point detail links shown above the concept panel.
    pane.querySelectorAll("[data-exam-point]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (handlers.selectExamPoint) handlers.selectExamPoint(button.getAttribute("data-exam-point"));
      });
    });
  }

  function renderOptionRows(state, question) {
    var keys = Object.keys(question.options || {}).sort();
    if (!keys.length) return empty("这道题暂无选项数据。");

    var html = '<div class="option-map">';
    keys.forEach(function (key, index) {
      var correct = String(question.answer || "").indexOf(key) >= 0;
      html += '<div class="option-row' + (correct ? " correct" : "") + '">';
      html += '<div class="option-key">' + U.escapeHtml(key) + "</div>";
      html += '<div class="option-copy">';
      html += '<p class="option-text">' + U.escapeHtml(question.options[key]) + "</p>";
      html += "</div></div>";
    });
    html += "</div>";
    return html;
  }

  function evidenceStatusLabel(status) {
    return {
      direct: "有明确原文",
      indirect: "需结合上下文",
      none: "待补原文",
      conflict: "依据冲突",
      needs_manual: "需人工"
    }[status] || status || "未标注";
  }

  function supportTypeLabel(type) {
    return {
      direct: "直接依据",
      indirect: "辅助依据",
      context: "背景",
      negative: "反驳"
    }[type] || type || "证据";
  }

  function judgementLabel(value) {
    return {
      correct: "正确",
      incorrect: "错误",
      insufficient: "证据不足",
      needs_manual: "需人工"
    }[value] || value || "未判断";
  }

  function questionEvidenceStatusLabel(status) {
    return {
      answered: "已生成",
      partial: "需复核",
      evidence_insufficient: "缺证据",
      parse_failed: "解析失败"
    }[status] || status || "未生成";
  }

  function questionEvidencePill(mapping) {
    if (!mapping) return '<span class="evidence-pill status-none">待补教材依据</span>';
    var cls = mapping.status === "answered" ? "status-direct" : "review";
    return '<span class="evidence-pill ' + cls + '">' + U.escapeHtml(questionEvidenceStatusLabel(mapping.status)) + "</span>";
  }

  function questionDirectoryEvidencePill(mapping) {
    if (!mapping) return '<span class="evidence-pill status-none">待补依据</span>';
    return "";
  }

  function renderIssueList(title, issues) {
    if (!issues || !issues.length) return "";
    var html = '<div class="option-review-note"><strong>' + U.escapeHtml(title) + "</strong>";
    issues.forEach(function (issue) {
      html += '<p>' + U.escapeHtml(typeof issue === "string" ? issue : JSON.stringify(issue)) + "</p>";
    });
    html += "</div>";
    return html;
  }

  function renderOptionEvidenceActions(questionId, evidence) {
    var qid = U.escapeHtml(questionId || "");
    var option = U.escapeHtml(evidence.option || "");
    var status = U.escapeHtml(evidence.evidence_status || "");
    var cardId = U.escapeHtml(((evidence.evidence_cards || [])[0] || {}).card_id || "");
    var html = '<div class="option-evidence-actions">';
    html += '<button class="fb-button confirm" type="button" data-option-fb-action="confirmed" data-fb-question="' + qid + '" data-fb-option="' + option + '" data-fb-status="' + status + '" data-fb-card="' + cardId + '">确认此选项证据</button>';
    html += '<button class="fb-button" type="button" data-option-fb-action="needs_evidence" data-fb-question="' + qid + '" data-fb-option="' + option + '" data-fb-status="' + status + '" data-fb-card="' + cardId + '">证据不够</button>';
    html += '<button class="fb-button reject" type="button" data-option-fb-action="wrong_card" data-fb-question="' + qid + '" data-fb-option="' + option + '" data-fb-status="' + status + '" data-fb-card="' + cardId + '">原文不对</button>';
    html += "</div>";
    return html;
  }

  function renderOptionEvidenceDetails(state, questionId, evidence) {
    var html = "";
    if ((evidence.evidence_cards || []).length) {
      html += '<div class="option-evidence-cards">';
      evidence.evidence_cards.forEach(function (card, index) {
        var canLocate = !!state.cardById[card.card_id];
        var pageLabel = getCardPageLabel(state, card);
        html += '<button class="evidence-card' + (canLocate ? "" : " candidate-only") + '" type="button" data-card="' + U.escapeHtml(card.card_id) + '">';
        html += '<span class="evidence-card-top">';
        html += '<span class="evidence-card-id">教材原文 ' + (index + 1) + (pageLabel ? " · " + U.escapeHtml(pageLabel) : "") + "</span>";
        html += '<span class="evidence-pill support-' + U.escapeHtml(card.support_type || "") + '">' + U.escapeHtml(supportTypeLabel(card.support_type)) + "</span>";
        if (card.relevance) html += '<span class="evidence-pill">' + U.escapeHtml(confidenceLabel(card.relevance)) + "</span>";
        html += "</span>";
        if (card.citation || card.quote) {
          html += '<span class="evidence-quote">' + U.escapeHtml(card.citation || card.quote) + "</span>";
        }
        if (card.reason) {
          html += '<span class="evidence-reason">' + U.escapeHtml(teacherText(card.reason)) + "</span>";
        }
        if (card.chapter_path || pageLabel) {
          html += '<span class="evidence-origin">' + U.escapeHtml(card.chapter_path || "未挂载") + "</span>";
        }
        html += "</button>";
      });
      html += "</div>";
    } else {
      html += '<div class="option-evidence-empty">这个选项还没有可引用教材原文，当前判断只能作为解析初稿。</div>';
    }

    if (evidence.explanation) {
      html += '<div class="option-analysis"><strong>解析口径</strong><p>' + U.escapeHtml(teacherText(evidence.explanation)) + "</p></div>";
    }
    if (evidence.common_trap) {
      html += '<div class="option-trap"><strong>易错点</strong><p>' + U.escapeHtml(teacherText(evidence.common_trap)) + "</p></div>";
    }
    if (evidence.teacher_review_reason) {
      html += '<div class="option-review-note">' + U.escapeHtml(teacherText(evidence.teacher_review_reason)) + "</div>";
    }
    html += renderOptionEvidenceActions(questionId, evidence);
    return html;
  }

  function renderOptionEvidenceLazyPayload(state, questionId, evidence) {
    return U.escapeHtml(JSON.stringify({
      html: renderOptionEvidenceDetails(state, questionId, evidence)
    }));
  }

  function renderOptionEvidenceCard(state, questionId, evidence) {
    var status = evidence.evidence_status || "none";
    var correct = evidence.is_correct_answer;
    var summary = evidence.common_trap || evidence.explanation || evidence.teacher_review_reason || "";
    var html = '<div class="option-evidence-row status-' + U.escapeHtml(status) + '">';
    html += '<div class="option-evidence-head">';
    html += '<div class="option-evidence-key">' + U.escapeHtml(evidence.option || "") + "</div>";
    html += '<div class="option-evidence-title">';
    html += '<p>' + U.escapeHtml(evidence.option_text || "") + "</p>";
    html += '<div class="option-evidence-meta">';
    html += '<span class="evidence-pill status-' + U.escapeHtml(status) + '">' + U.escapeHtml(evidenceStatusLabel(status)) + "</span>";
    html += '<span class="evidence-pill">' + U.escapeHtml(judgementLabel(evidence.judgement)) + "</span>";
    if (correct) html += '<span class="evidence-pill correct">标准答案</span>';
    if (evidence.needs_teacher_review) html += '<span class="evidence-pill review">教研复核</span>';
    html += "</div></div></div>";
    if (summary) {
      html += '<p class="option-evidence-summary-line">' + U.escapeHtml(U.shortText(teacherText(summary), 140)) + "</p>";
    }
    html += '<details class="option-detail" data-option-detail data-option-payload="' + renderOptionEvidenceLazyPayload(state, questionId, evidence) + '">';
    html += '<summary>展开证据与解析</summary><div class="option-detail-body"></div></details>';
    html += "</div>";
    return html;
  }

  function renderQuestionOptionEvidence(state, question) {
    var mapping = Store.getOptionEvidenceForQuestion(state, question.id);
    var html = '<div class="panel-section"><div class="panel-section-header">选项与原文依据</div>';
    if (!mapping) {
      html += '<div class="panel-section-body">';
      html += '<p class="reference-note">本题还没有整理到每个选项的教材依据，当前只能作为解析初稿。</p>';
      html += "</div></div>";
      return html;
    }

    (mapping.options || []).forEach(function (option) {
      html += renderOptionEvidenceCard(state, question.id, option);
    });
    html += "</div>";
    return html;
  }

  function renderQaAiEvidencePreview(state, evidence) {
    var cards = (evidence.evidence_cards || []).slice(0, 2);
    if (!cards.length) {
      return '<p class="qa-ai-empty">暂无可引用教材原文，当前判断只适合作为人工复核线索。</p>';
    }
    var html = '<details class="qa-ai-evidence"><summary>查看依据</summary><div class="qa-ai-evidence-list">';
    cards.forEach(function (card) {
      html += '<div class="qa-ai-evidence-card">';
      html += '<span>' + U.escapeHtml(evidenceDisplayName(state, card, "教材原文")) + '</span>';
      html += '<p>' + U.escapeHtml(U.shortText(card.citation || card.quote || card.reason || "", 150)) + '</p>';
      html += '</div>';
    });
    html += '</div></details>';
    return html;
  }

  function renderQaAiAssistantAnalysis(state, context) {
    if (!context || !context.id || !Store.getOptionEvidenceForQuestion) return "";
    var mapping = Store.getOptionEvidenceForQuestion(state, context.id);
    if (!mapping || !(mapping.options || []).length) return "";
    var status = mapping.status || "";
    var html = '<details class="panel-section qa-ai-section">';
    html += '<summary class="panel-section-header">AI 辅助解析</summary>';
    html += '<div class="panel-section-body compact-body">';

    html += '<div class="qa-ai-meta">';
    html += '<span class="evidence-pill ' + (status === "answered" ? "status-direct" : "review") + '">' + U.escapeHtml(questionEvidenceStatusLabel(status)) + '</span>';
    html += '<span class="evidence-pill">题 ' + U.escapeHtml(context.id) + '</span>';
    html += '</div></div>';
    (mapping.options || []).forEach(function (evidence) {
      var option = evidence.option || "";
      var status = evidence.evidence_status || "none";
      var summary = evidence.evidence_status === "none"
        ? "暂无可引用教材原文，需人工判断。"
        : (evidence.explanation || evidence.common_trap || evidence.teacher_review_reason || "");
      html += '<div class="qa-ai-option status-' + U.escapeHtml(status) + '">';
      html += '<div class="qa-ai-option-head">';
      html += '<span class="option-evidence-key">' + U.escapeHtml(option) + '</span>';
      html += '<div><p>' + U.escapeHtml(evidence.option_text || "") + '</p><div class="option-evidence-meta">';
      html += '<span class="evidence-pill status-' + U.escapeHtml(status) + '">' + U.escapeHtml(evidenceStatusLabel(status)) + '</span>';
      html += '<span class="evidence-pill">' + U.escapeHtml(judgementLabel(evidence.judgement)) + '</span>';
      if (evidence.is_correct_answer) html += '<span class="evidence-pill correct">标准答案</span>';
      if (evidence.needs_teacher_review || status !== "direct") html += '<span class="evidence-pill review">需复核</span>';
      html += '</div></div></div>';
      html += '<p class="qa-ai-summary">' + U.escapeHtml(U.shortText(teacherText(summary), 170)) + '</p>';
      if (evidence.common_trap && status !== "none") {
        html += '<p class="qa-ai-trap"><strong>易错点</strong> ' + U.escapeHtml(U.shortText(evidence.common_trap, 130)) + '</p>';
      }
      html += renderQaAiEvidencePreview(state, evidence);
      html += '</div>';
    });
    html += '</details>';
    return html;
  }

  function renderQuestionEvidence(state, question) {
    var mapping = state.questionMap[question.id] || {};
    var cardIds = mapping.matched_card_ids || [];
    var concepts = getQuestionConcepts(state, question.id);
    var html = "";

    if (concepts.length) {
      html += '<div class="panel-section"><div class="panel-section-header">可能相关的教材区域</div><div class="panel-section-body">';
      html += '<p class="reference-note">这里只用于辅助定位教材区域，不能直接作为选项解析或教研诊断依据。</p>';
      html += '<div class="node-list">';
      concepts.slice(0, 10).forEach(function (section) {
        html += '<button class="node-chip" type="button" data-section="' + U.escapeHtml(section) + '">' + U.escapeHtml(section) + "</button>";
      });
      html += "</div></div></div>";
    }

    if (cardIds.length) {
      html += '<div class="panel-section"><div class="panel-section-header">可能相关的原文</div>';
      html += '<div class="panel-section-body compact-body"><p class="reference-note">这些原文只是辅助定位，尚未确认到 A/B/C/D 每个选项。</p></div>';
      cardIds.slice(0, 8).forEach(function (cid) {
        var card = state.cardById[cid];
        if (!card) return;
        html += '<button class="related-card" type="button" data-card="' + U.escapeHtml(cid) + '">';
        html += '<p class="related-title">' + U.escapeHtml(card.knowledge || cid) + "</p>";
        html += '<p class="related-meta">' + U.escapeHtml(state.cardToSection[cid] || "未挂载") + " · " + U.escapeHtml(cid) + "</p>";
        html += "</button>";
      });
      html += "</div>";
    }

    return html;
  }

  function renderQuestionRelations(state, question) {
    var concepts = getQuestionConcepts(state, question.id);
    if (concepts.length < 2) return "";
    var edges = [];
    concepts.forEach(function (from) {
      (state.sectionEdges[from] || []).forEach(function (edge) {
        if (concepts.indexOf(edge.target) >= 0) edges.push({ from: from, edge: edge });
      });
    });
    if (!edges.length) return "";
    var seen = {};
    var html = '<div class="detail-box"><h4>可能相关的知识关系</h4>';
    html += '<p class="reference-note">这里是辅助理解的关系线索，不代表选项之间的真实判题关系。</p>';
    edges.slice(0, 4).forEach(function (row) {
      var key = [row.from, row.edge.target, row.edge.type].sort().join("|");
      if (seen[key]) return;
      seen[key] = true;
      html += '<p><strong>' + U.escapeHtml(row.edge.type || "关系") + '</strong>：' + U.escapeHtml(row.from) + " → " + U.escapeHtml(row.edge.target) + "。";
      html += U.escapeHtml(row.edge.detail || "") + "</p>";
    });
    html += "</div>";
    return html;
  }

  function renderExamPointListMeta(ep) {
    var chips = [];
    var questionCount = (ep.question_ids || []).length;
    var qaCount = (ep.qa_ids || []).length;
    var sourceCount = getTotalSourceCount(ep);
    if (questionCount) chips.push(questionCount + " 道题");
    if (qaCount) chips.push(qaCount + " 条答疑");
    if (sourceCount) chips.push(sourceCount + " 条原文依据");
    if (!chips.length) return "";
    return '<span class="exam-point-meta">' + chips.map(function (item) {
      return '<span>' + U.escapeHtml(item) + "</span>";
    }).join("") + "</span>";
  }

  function renderQuestionExamPoints(state, question) {
    var eps = Store.getExamPointsForQuestion(state, question.id);
    if (!eps.length) return "";
    var html = '<div class="panel-section"><div class="panel-section-header">关联考点 · ' + eps.length + "</div>";
    eps.forEach(function (ep) {
      var priority = getExamPointPriority(ep);
      html += '<button class="exam-point-card priority-' + U.escapeHtml(priority) + '" type="button" data-exam-point="' + U.escapeHtml(ep.id) + '">';
      html += '<span class="exam-point-row-head">';
      html += '<span class="exam-point-title">' + U.escapeHtml(ep.title || ep.id) + "</span>";
      html += '<span class="exam-point-chevron" aria-hidden="true">›</span>';
      html += "</span>";
      html += '<span class="exam-point-row-meta">';
      html += renderExamPointListMeta(ep);
      html += "</span>";

      html += "</button>";
    });
    html += "</div>";
    return html;
  }

  function renderQuestionDetail(state, qid, handlers, options) {
    var pane = getPane();
    var question = state.questionById[qid];
    if (!pane || !question) return;

    var html = '<div class="panel-scroll">';
    html += renderPanelHeadStart(options);
    html += '<div class="panel-meta">' + pill(qid) + "</div>";
    html += '<h2 class="panel-title">' + U.escapeHtml(question.stem || qid) + "</h2>";
    html += "</div></div>";
    html += '<div class="panel-body">';
    html += '<div class="panel-section"><div class="panel-section-header">题目选项</div><div class="panel-section-body">';
    html += renderOptionRows(state, question);
    html += "</div></div>";
    html += renderQuestionExamPoints(state, question);
    html += renderQuestionOptionEvidence(state, question);
    html += "</div></div>";

    pane.innerHTML = html;
    bindBackEvent(pane, handlers);
    pane.querySelectorAll("[data-section]").forEach(function (button) {
      button.addEventListener("click", function () {
        handlers.selectSection(button.getAttribute("data-section"), { scroll: false });
      });
    });
    pane.querySelectorAll("[data-card]").forEach(function (button) {
      button.addEventListener("click", function () {
        handlers.selectCard(button.getAttribute("data-card"), { scroll: button.classList.contains("evidence-card") });
      });
    });
    pane.querySelectorAll("[data-exam-point]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (handlers.selectExamPoint) handlers.selectExamPoint(button.getAttribute("data-exam-point"));
      });
    });
    pane.querySelectorAll("[data-option-fb-action]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (!handlers.submitOptionFeedback) return;
        handlers.submitOptionFeedback(
          button.getAttribute("data-fb-question"),
          button.getAttribute("data-fb-option"),
          button.getAttribute("data-option-fb-action"),
          button.getAttribute("data-fb-card"),
          button.getAttribute("data-fb-status")
        );
      });
    });
    bindOptionDetailEvents(pane, handlers);
  }

  function renderQuestionList(state, handlers, activeFilter, options) {
    var pane = getPane();
    if (!pane) return;
    activeFilter = activeFilter || "all";
    var filteredQuestions = state.questions.filter(function (question) {
      var profile = getQuestionProfile(state, question);
      if (activeFilter === "generated") return profile.hasEvidence;
      if (activeFilter === "missing") return !profile.hasEvidence;
      if (activeFilter === "traps") return profile.hasTrap;
      if (activeFilter === "issues") return profile.hasIssues || profile.hasNoneEvidence;
      return true;
    });
    var grouped = {};
    filteredQuestions.forEach(function (question) {
      var key = question.section || "未分节";
      if (!grouped[key]) grouped[key] = [];
      grouped[key].push(question);
    });
    var counts = {
      all: state.questions.length,
      generated: state.questions.filter(function (q) { return getQuestionProfile(state, q).hasEvidence; }).length,
      missing: state.questions.filter(function (q) { return !getQuestionProfile(state, q).hasEvidence; }).length,
      traps: state.questions.filter(function (q) { return getQuestionProfile(state, q).hasTrap; }).length,
      issues: state.questions.filter(function (q) {
        var profile = getQuestionProfile(state, q);
        return profile.hasIssues || profile.hasNoneEvidence;
      }).length
    };
    var filters = [
      { id: "all", label: "全部", count: counts.all },
      { id: "generated", label: "有依据", count: counts.generated },
      { id: "missing", label: "待补依据", count: counts.missing },
      { id: "traps", label: "易错题", count: counts.traps },
      { id: "issues", label: "需检查", count: counts.issues }
    ];

    var html = '<div class="panel-scroll">';
    html += renderPanelHeadStart(options);
    html += '<div class="panel-meta"><span class="mode-label">题目教研</span>' + pill(filteredQuestions.length + " / " + state.questions.length + " 道题", "blue") + "</div>";
    html += '<h2 class="panel-title">题目解析目录</h2>';
    html += '<p class="panel-citation">按解析状态、易错点和待补依据筛选题目。</p>';
    html += renderFilterBar("question", filters, activeFilter);
    html += "</div></div>";
    html += '<div class="panel-body">';
    Object.keys(grouped).sort().forEach(function (section) {
      html += '<div class="panel-section"><div class="panel-section-header">' + U.escapeHtml(section) + " · " + grouped[section].length + " 题</div>";
      grouped[section].forEach(function (question, index) {
        var profile = getQuestionProfile(state, question);
        var flags = [];
        if (profile.hasTrap && activeFilter !== "traps") flags.push({ label: "易错" });
        if (profile.hasIssues) flags.push({ label: "需检查", cls: "danger-text" });
        html += renderQuestionCard(question, index, { showOptions: false, state: state, flags: flags, compactList: true });
      });
      html += "</div>";
    });
    if (!filteredQuestions.length) {
      html += '<div class="panel-section"><div class="panel-section-body">' + empty("当前筛选下暂无题目。") + "</div></div>";
    }
    html += "</div></div>";

    pane.innerHTML = html;
    bindBackEvent(pane, handlers);
    pane.querySelectorAll("[data-question]").forEach(function (button) {
      button.addEventListener("click", function () {
        handlers.selectQuestion(button.getAttribute("data-question"));
      });
    });
    bindFilterEvents(pane, handlers);
  }

  function renderQaDetail(state, qaid, handlers, options) {
    var pane = getPane();
    var record = state.qaById[qaid];
    if (!pane || !record) return;
    var eps = Store.getExamPointsForQa ? Store.getExamPointsForQa(state, qaid) : [];
    var context = getQaQuestionContext(state, record);
    var doubt = getQaStudentDoubt(record);
    var reply = getQaReplyText(record, doubt);
    var bodyText = teacherText(record.full_text || record.core_point || "");

    var html = '<div class="panel-scroll">';
    html += renderPanelHeadStart(options);
    html += '<h2 class="panel-title">学生疑问笔记</h2>';
    html += "</div></div>";
    html += '<div class="panel-body">';

    html += '<div class="panel-section qa-question-context"><div class="panel-section-header">题目背景</div><div class="panel-section-body">';
    html += '<p class="qa-context-stem">' + U.escapeHtml(context.stem || record.question || record.id) + "</p>";
    html += '<div class="qa-context-meta">';
    if (context.id) html += '<span>题 ' + U.escapeHtml(context.id) + "</span>";
    if (context.answer) html += '<span>答案 ' + U.escapeHtml(context.answer) + "</span>";
    html += "</div>";
    html += renderQaCompactOptions(context, doubt);
    html += "</div></div>";

    html += '<div class="panel-section qa-doubt-section"><div class="panel-section-header">学生疑问</div><div class="panel-section-body">';
    html += '<p class="qa-detail-question">' + U.escapeHtml(doubt) + "</p>";
    html += "</div></div>";

    if (reply) {
      html += '<div class="panel-section"><div class="panel-section-header">教研解析</div><div class="panel-section-body">';
      html += renderQaReplyAnalysis(reply);
      html += "</div></div>";
    }
    html += renderQaAiAssistantAnalysis(state, context);
    if (eps.length) {
      html += '<div class="panel-section"><div class="panel-section-header">关联考点 · ' + eps.length + "</div>";
      eps.forEach(function (ep) {
        html += '<button class="exam-point-card compact-card priority-' + U.escapeHtml(getExamPointPriority(ep)) + '" type="button" data-exam-point="' + U.escapeHtml(ep.id || "") + '">';
        html += '<span class="exam-point-row-head"><span class="exam-point-title">' + U.escapeHtml(ep.title || ep.id) + '</span><span class="exam-point-chevron" aria-hidden="true">›</span></span>';
        html += "</button>";
      });
      html += "</div>";
    }
    html += "</div></div>";

    pane.innerHTML = html;
    bindBackEvent(pane, handlers);
    bindSharedPanelEvents(pane, handlers);
  }

  function renderGraphModal(state, cid, handlers) {
    var card = state.cardById[cid];
    var concept = card && Store.getCardSection(state, cid);
    if (!concept) return;
    var old = U.byId("graphModal");
    if (old) old.remove();

    var width = 820;
    var height = 430;
    var cx = width / 2;
    var cy = height / 2;
    var radius = 145;
    var edges = concept.edges.slice(0, 8);

    var html = '<div class="modal-backdrop" id="graphModal">';
    html += '<div class="graph-modal">';
    html += '<div class="graph-modal-head"><h3>' + U.escapeHtml(concept.name) + '</h3><button class="icon-button" type="button" data-close-modal>×</button></div>';
    html += '<div class="graph-canvas">';
    html += '<svg class="graph-svg" viewBox="0 0 ' + width + " " + height + '" aria-hidden="true">';
    edges.forEach(function (edge, index) {
      var angle = (-90 + index * (360 / Math.max(edges.length, 1))) * Math.PI / 180;
      var x = cx + Math.cos(angle) * radius;
      var y = cy + Math.sin(angle) * radius;
      html += '<line x1="' + cx + '" y1="' + cy + '" x2="' + x + '" y2="' + y + '" stroke="#cbd5e1" stroke-width="1.5" />';
    });
    html += "</svg>";
    html += '<button class="graph-bubble current" type="button" style="left:50%;top:50%">' + U.escapeHtml(concept.name) + "</button>";
    edges.forEach(function (edge, index) {
      var angle = (-90 + index * (360 / Math.max(edges.length, 1))) * Math.PI / 180;
      var x = cx + Math.cos(angle) * radius;
      var y = cy + Math.sin(angle) * radius;
      var lx = cx + Math.cos(angle) * (radius * 0.52);
      var ly = cy + Math.sin(angle) * (radius * 0.52);
      html += '<button class="graph-bubble" type="button" data-modal-section="' + U.escapeHtml(edge.target) + '" style="left:' + (x / width * 100) + "%;top:" + (y / height * 100) + '%">' + U.escapeHtml(edge.target) + "</button>";
      html += '<span class="graph-edge-label" style="left:' + (lx / width * 100) + "%;top:" + (ly / height * 100) + '%">' + U.escapeHtml(edge.type || "关系") + "</span>";
    });
    html += "</div></div></div>";

    document.body.insertAdjacentHTML("beforeend", html);
    var modal = U.byId("graphModal");
    modal.querySelector("[data-close-modal]").addEventListener("click", function () {
      modal.remove();
    });
    modal.addEventListener("click", function (event) {
      if (event.target === modal) modal.remove();
    });
    modal.querySelectorAll("[data-modal-section]").forEach(function (button) {
      button.addEventListener("click", function () {
        modal.remove();
        handlers.selectSection(button.getAttribute("data-modal-section"), { scroll: false });
      });
    });
  }

  window.CamsPanel = {
    render: renderConcept,
    renderExamPointDetail: renderExamPointDetail,
    renderExamPointList: renderExamPointList,
    renderGraphModal: renderGraphModal,
    renderQaDetail: renderQaDetail,
    renderWorkbenchHome: renderWorkbenchHome,
    renderQuestionDetail: renderQuestionDetail,
    renderQuestionList: renderQuestionList
  };
})();
