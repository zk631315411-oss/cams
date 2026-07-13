(function () {
  var U = window.CamsUtils;

  function getJson(path) {
    return fetch(path).then(function (res) {
      if (!res.ok) throw new Error(path + " 加载失败: " + res.status);
      return res.json();
    });
  }

  function createEmptyState() {
    return {
      chapter: null,
      cards: [],
      questions: [],
      qaRecords: [],
      qaBindings: [],
      questionMap: {},
      cardRelations: {},
      kgData: {},
      cardById: {},
      questionById: {},
      qaById: {},
      qaBindingById: {},
      cardToQuestions: {},
      cardToQa: {},
      cardToSection: {},
      sectionInfo: {},
      sectionToCards: {},
      sectionEdges: {},
      paragraphByCard: {},
      paragraphs: [],
      examPoints: [],
      examPointById: {},
      examPointByCardId: {},
      examPointByQuestionId: {},
      examPointByQaId: {},
      optionEvidence: [],
      optionEvidenceByQuestionId: {},
      sentenceExamPointMap: {},
      cardPageMap: {},
      stats: {}
    };
  }

  function pushUnique(map, key, value) {
    if (!key || !value) return;
    if (!map[key]) map[key] = [];
    if (map[key].indexOf(value) < 0) map[key].push(value);
  }

  function buildQuestionIndexes(state) {
    Object.keys(state.questionMap).forEach(function (qid) {
      var mapping = state.questionMap[qid] || {};
      (mapping.matched_card_ids || []).forEach(function (cid) {
        pushUnique(state.cardToQuestions, cid, qid);
      });
    });
  }

  function buildQaIndexes(state) {
    state.qaRecords.forEach(function (record) {
      state.qaById[record.id] = record;
    });

    state.qaBindings.forEach(function (binding) {
      if (binding.qa_id) state.qaBindingById[binding.qa_id] = binding;
      (binding.inherited_card_ids || []).forEach(function (cid) {
        if (!state.cardToQa[cid]) state.cardToQa[cid] = [];
        state.cardToQa[cid].push({
          binding: binding,
          record: state.qaById[binding.qa_id] || null
        });
      });
    });
  }

  function buildKgIndexes(state) {
    var kg = state.kgData || {};
    state.sectionInfo = kg._sections || {};

    Object.keys(kg).forEach(function (key) {
      if (key.charAt(0) === "_") return;
      var row = kg[key] || {};
      if (!row.section) return;
      state.cardToSection[key] = row.section;
      pushUnique(state.sectionToCards, row.section, key);
    });

    Object.keys(state.sectionInfo).forEach(function (sectionName) {
      if (!state.sectionToCards[sectionName]) state.sectionToCards[sectionName] = [];
    });

    (kg._edges || []).forEach(function (edge) {
      if (!edge || !edge.from || !edge.to) return;
      if (!state.sectionEdges[edge.from]) state.sectionEdges[edge.from] = [];
      if (!state.sectionEdges[edge.to]) state.sectionEdges[edge.to] = [];
      state.sectionEdges[edge.from].push({
        target: edge.to,
        type: edge.type,
        detail: edge.detail,
        direction: "out"
      });
      state.sectionEdges[edge.to].push({
        target: edge.from,
        type: edge.type,
        detail: edge.detail,
        direction: "in"
      });
    });

    Object.keys(kg).forEach(function (key) {
      if (key.charAt(0) === "_") return;
      var row = kg[key] || {};
      var sectionName = row.section;
      if (!sectionName || state.sectionEdges[sectionName]) return;
      state.sectionEdges[sectionName] = (row.edges || []).map(function (edge) {
        return {
          target: edge.target,
          type: edge.type,
          detail: edge.detail,
          direction: "out"
        };
      });
    });
  }

  function buildReaderIndexes(state) {
    var paragraphs = [];
    var chapter = state.chapter || {};
    (chapter.sections || []).forEach(function (section) {
      (section.subsections || []).forEach(function (subsection, subIndex) {
        (subsection.paragraphs || []).forEach(function (paragraph, pIndex) {
          var id = "p-" + paragraphs.length;
          var row = {
            id: id,
            sectionId: section.section_id,
            sectionTitle: section.section_title,
            subsectionTitle: subsection.title || "",
            subsectionIndex: subIndex,
            paragraphIndex: pIndex,
            text: paragraph.text || "",
            cardIds: paragraph.card_ids || [],
            highlightCardIds: paragraph.highlight_card_ids || []
          };
          paragraphs.push(row);
          row.cardIds.forEach(function (cid) {
            if (!state.paragraphByCard[cid]) state.paragraphByCard[cid] = row;
          });
          row.highlightCardIds.forEach(function (cid) {
            if (!state.paragraphByCard[cid]) state.paragraphByCard[cid] = row;
          });
        });
      });
    });
    state.paragraphs = paragraphs;
  }

  function attachFallbackSections(state) {
    state.cards.forEach(function (card) {
      if (state.cardToSection[card.card_id]) return;
      var paragraph = state.paragraphByCard[card.card_id];
      if (!paragraph || !paragraph.subsectionTitle) return;
      state.cardToSection[card.card_id] = paragraph.subsectionTitle;
      pushUnique(state.sectionToCards, paragraph.subsectionTitle, card.card_id);
      if (!state.sectionInfo[paragraph.subsectionTitle]) {
        state.sectionInfo[paragraph.subsectionTitle] = {
          definition: "",
          aliases: [],
          card_count: state.sectionToCards[paragraph.subsectionTitle].length
        };
      }
    });
  }

  function buildExamPointIndexes(state) {
    (state.examPoints || []).forEach(function (ep) {
      state.examPointById[ep.id] = ep;
      (ep.source_card_ids || []).forEach(function (cid) {
        pushUnique(state.examPointByCardId, cid, ep.id);
      });
      (ep.question_ids || []).forEach(function (qid) {
        pushUnique(state.examPointByQuestionId, qid, ep.id);
      });
      (ep.qa_ids || []).forEach(function (qaid) {
        pushUnique(state.examPointByQaId, qaid, ep.id);
      });
    });
  }

  function buildOptionEvidenceIndexes(state) {
    (state.optionEvidence || []).forEach(function (item) {
      if (!item || !item.question_id) return;
      state.optionEvidenceByQuestionId[item.question_id] = item;
    });
  }

  function buildState(payload) {
    var state = createEmptyState();
    state.chapter = payload.chapter;
    state.cards = Array.isArray(payload.cards) ? payload.cards : ((payload.cards && payload.cards.cards) || []);
    state.questions = (payload.questions && payload.questions.questions) || [];
    state.qaRecords = (payload.qa && payload.qa.records) || [];
    state.qaBindings = (payload.qaBindings && payload.qaBindings.bindings) || [];
    state.questionMap = (payload.questionMap && payload.questionMap.mappings) || {};
    state.cardRelations = payload.cardRelations || {};
    state.kgData = payload.kgData || {};
    state.examPoints = (payload.examPoints && payload.examPoints.exam_points) || [];
    state.optionEvidence = (payload.optionEvidence && payload.optionEvidence.items) || [];
    state.sentenceExamPointMap = payload.sentenceExamPointMap || {};
    state.cardPageMap = (payload.cardPageMap && payload.cardPageMap.cards) || {};

    state.cards.forEach(function (card) {
      state.cardById[card.card_id] = card;
    });
    state.questions.forEach(function (question) {
      state.questionById[question.id] = question;
    });

    buildReaderIndexes(state);
    buildQuestionIndexes(state);
    buildQaIndexes(state);
    buildKgIndexes(state);
    buildExamPointIndexes(state);
    buildOptionEvidenceIndexes(state);
    attachFallbackSections(state);

    state.stats = {
      sections: (state.chapter.sections || []).length,
      cards: state.cards.length,
      questions: state.questions.length,
      qa: state.qaRecords.length,
      optionEvidenceQuestions: state.optionEvidence.length,
      mappedExamPointParagraphs: ((state.sentenceExamPointMap.stats || {}).paragraphs_with_exam_points) || 0,
      paragraphs: state.paragraphs.length,
      kgSections: Object.keys(state.sectionInfo).length,
      kgEdges: ((state.kgData || {})._edges || []).length
    };

    return state;
  }

  function load() {
    var base = "data/teaching_assets/";
    var legacyBase = "data/";
    function getPrimary(path, fallbackPath, fallbackValue) {
      return getJson(base + path).catch(function () {
        if (!fallbackPath) return fallbackValue;
        return getJson(legacyBase + fallbackPath).catch(function () { return fallbackValue; });
      });
    }
    return Promise.all([
      getPrimary("chapters/v6_full.json", "chapters/v6.json"),
      getPrimary("cards_v6_sentence.json", "cards_v6_sentence.json"),
      getPrimary("questions.json", "questions.json"),
      getPrimary("qa.json", "qa.json"),
      getPrimary("qa_bindings.json", "qa_bindings.json"),
      getPrimary("question_card_map.json", "question_card_map.json"),
      getPrimary("card_relations.json", "card_relations.json", {}),
      getPrimary("kg_data.json", "kg_data.json", {}),
      Promise.resolve({ exam_points: [] }),
      getPrimary("option_evidence_map.json", "option_evidence_map.json", { items: [] }),
      Promise.resolve({ stats: {}, paragraphs: [], sentences: [] }),
      getJson("data/page_maps/card_page_map_v6.json").catch(function () { return { cards: {} }; })
    ]).then(function (items) {
      return buildState({
        chapter: items[0],
        cards: items[1],
        questions: items[2],
        qa: items[3],
        qaBindings: items[4],
        questionMap: items[5],
        cardRelations: items[6],
        kgData: items[7],
        examPoints: items[8],
        optionEvidence: items[9],
        sentenceExamPointMap: items[10],
        cardPageMap: items[11]
      });
    });
  }

  function getCardsForSection(state, sectionName, limit) {
    var ids = (state.sectionToCards[sectionName] || []).slice(0, limit || 20);
    return ids.map(function (cid) { return state.cardById[cid]; }).filter(Boolean);
  }

  function getBestCardForSection(state, sectionName) {
    var ids = state.sectionToCards[sectionName] || [];
    for (var i = 0; i < ids.length; i += 1) {
      if (state.paragraphByCard[ids[i]]) return ids[i];
    }
    return ids[0] || null;
  }

  function getCardSection(state, cid) {
    var sectionName = state.cardToSection[cid];
    if (!sectionName) return null;
    return {
      name: sectionName,
      info: state.sectionInfo[sectionName] || {},
      edges: U.unique((state.sectionEdges[sectionName] || []).map(function (edge) {
        return JSON.stringify(edge);
      })).map(function (raw) { return JSON.parse(raw); })
    };
  }

  function getExamPointsForCard(state, cid) {
    var ids = state.examPointByCardId[cid] || [];
    return ids.map(function (epid) { return state.examPointById[epid]; }).filter(Boolean);
  }

  function getExamPoint(state, epid) {
    return state.examPointById[epid] || null;
  }

  function getExamPointsForQuestion(state, qid) {
    var ids = state.examPointByQuestionId[qid] || [];
    return ids.map(function (epid) { return state.examPointById[epid]; }).filter(Boolean);
  }

  function getQuestionsForExamPoint(state, ep) {
    return ((ep && ep.question_ids) || []).map(function (qid) {
      return state.questionById[qid];
    }).filter(Boolean);
  }

  function getCardsForExamPoint(state, ep) {
    return ((ep && ep.source_card_ids) || []).map(function (cid) {
      return state.cardById[cid];
    }).filter(Boolean);
  }

  function getQaForExamPoint(state, ep) {
    return ((ep && ep.qa_ids) || []).map(function (qaid) {
      return state.qaById[qaid];
    }).filter(Boolean);
  }

  function getExamPointsForQa(state, qaid) {
    var ids = (state.examPointByQaId[qaid] || []).slice();
    var binding = state.qaBindingById[qaid] || {};
    if (binding.bound_question_id) {
      (state.examPointByQuestionId[binding.bound_question_id] || []).forEach(function (epid) {
        if (ids.indexOf(epid) < 0) ids.push(epid);
      });
    }
    (binding.inherited_card_ids || []).forEach(function (cid) {
      (state.examPointByCardId[cid] || []).forEach(function (epid) {
        if (ids.indexOf(epid) < 0) ids.push(epid);
      });
    });
    return ids.map(function (epid) { return state.examPointById[epid]; }).filter(Boolean);
  }

  function getQaBinding(state, qaid) {
    return state.qaBindingById[qaid] || null;
  }

  function getOptionEvidenceForQuestion(state, qid) {
    return state.optionEvidenceByQuestionId[qid] || null;
  }

  window.CamsStore = {
    getBestCardForSection: getBestCardForSection,
    getCardsForExamPoint: getCardsForExamPoint,
    getCardsForSection: getCardsForSection,
    getCardSection: getCardSection,
    getExamPoint: getExamPoint,
    getExamPointsForCard: getExamPointsForCard,
    getExamPointsForQa: getExamPointsForQa,
    getExamPointsForQuestion: getExamPointsForQuestion,
    getOptionEvidenceForQuestion: getOptionEvidenceForQuestion,
    getQaBinding: getQaBinding,
    getQaForExamPoint: getQaForExamPoint,
    getQuestionsForExamPoint: getQuestionsForExamPoint,
    load: load
  };
})();
