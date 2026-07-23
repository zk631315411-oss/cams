/* ═══════════════════════════════════════════
   题-单元映射表矩阵页面
   独立全屏页面，展示题目与教材知识单元的映射关系
   ═══════════════════════════════════════════ */
(function () {
  var U = window.CamsUtils;

  /**
   * 从 evidence 构建题-单元映射索引
   * 返回值: { question_id -> [{ unit_id, support_type }] }
   */
  function buildMatrix(state) {
    var map = {};
    (state.evidence || []).forEach(function (ev) {
      var qid = ev.question_id;
      if (!qid) return;
      var list = map[qid] || (map[qid] = []);
      var seen = {};
      (ev.option_analysis || []).forEach(function (option) {
        (option.evidence_cards || []).forEach(function (card) {
          if (!card.unit_id) return;
          // 同一题同单元只保留一条记录，避免重复
          var key = card.unit_id + "|" + (card.support_type || "direct");
          if (seen[key]) return;
          seen[key] = true;
          list.push({ unit_id: card.unit_id, support_type: card.support_type || "direct" });
        });
      });
    });
    return map;
  }

  /**
   * 根据 support_type 返回对应的 CSS class
   */
  function strengthClass(type) {
    if (type === "direct") return "strength-direct";
    if (type === "indirect") return "strength-indirect";
    if (type === "context") return "strength-context";
    return "strength-direct";
  }

  /**
   * 渲染单元标签
   */
  function renderUnitTags(units, unitMap) {
    return units.map(function (item) {
      var unit = unitMap[item.unit_id] || {};
      var label = unit.zh_display_text || item.unit_id;
      var cls = strengthClass(item.support_type);
      return '<span class="unit-tag ' + cls + '" title="' + U.escapeHtml(label) + '">' + U.escapeHtml(item.unit_id) + "</span>";
    }).join("");
  }

  /**
   * 渲染表格行
   */
  function renderRows(questions, matrix, unitMap) {
    return questions.map(function (q) {
      var units = matrix[q.question_id] || [];
      var stem = q.stem_zh || q.stem_en || "";
      var stemShort = U.shortText(stem, 80);
      return (
        '<tr data-question-id="' + U.escapeHtml(q.question_id) + '">' +
          '<td class="col-id">' + U.escapeHtml(q.question_id) + "</td>" +
          '<td class="col-stem" title="' + U.escapeHtml(stem) + '">' + U.escapeHtml(stemShort) + "</td>" +
          '<td class="col-units">' + renderUnitTags(units, unitMap) + "</td>" +
        "</tr>"
      );
    }).join("");
  }

  /**
   * 构建单元筛选下拉选项
   */
  function renderUnitOptions(units) {
    return units.map(function (u) {
      var label = u.zh_display_text || u.unit_id;
      return '<option value="' + U.escapeHtml(u.unit_id) + '">' + U.escapeHtml(label) + "</option>";
    }).join("");
  }

  /**
   * 对表格行进行筛选过滤
   */
  function filterRows(questions, matrix, searchTerm, unitFilter, strengthFilter) {
    var lowerSearch = U.normalizeText(searchTerm);
    return questions.filter(function (q) {
      // 搜索过滤
      if (lowerSearch) {
        var idMatch = U.normalizeText(q.question_id).indexOf(lowerSearch) >= 0;
        var stemMatch = U.normalizeText(q.stem_zh || "").indexOf(lowerSearch) >= 0;
        if (!idMatch && !stemMatch) return false;
      }
      var units = matrix[q.question_id] || [];
      // 单元过滤：只显示涉及该单元的题目
      if (unitFilter) {
        var hasUnit = units.some(function (u) { return u.unit_id === unitFilter; });
        if (!hasUnit) return false;
      }
      // 强度过滤：只显示包含该强度关联的题目
      if (strengthFilter) {
        var hasStrength = units.some(function (u) { return u.support_type === strengthFilter; });
        if (!hasStrength) return false;
      }
      return true;
    });
  }

  /**
   * 导出 Excel
   */
  function exportExcel(state, questions, matrix) {
    if (typeof XLSX === "undefined") {
      // 动态加载 SheetJS
      var script = document.createElement("script");
      script.src = "https://cdn.sheetjs.com/xlsx-0.20.1/package/dist/xlsx.full.min.js";
      script.onload = function () { doExport(state, questions, matrix); };
      script.onerror = function () { alert("无法加载 Excel 导出库，请检查网络连接。"); };
      document.head.appendChild(script);
    } else {
      doExport(state, questions, matrix);
    }
  }

  function doExport(state, questions, matrix) {
    // 表头
    var data = [["题目ID", "题干", "题型", "涉及 Unit/CP", "支持强度"]];
    // 每行展开为多行：一道题涉及 N 个单元就展 N 行
    questions.forEach(function (q) {
      var units = matrix[q.question_id] || [];
      if (units.length === 0) {
        // 无关联的题也占一行
        data.push([q.question_id, q.stem_zh || "", q.type || "", "", ""]);
      } else {
        units.forEach(function (u) {
          data.push([q.question_id, q.stem_zh || "", q.type || "", u.unit_id, u.support_type]);
        });
      }
    });
    var wb = XLSX.utils.book_new();
    var ws = XLSX.utils.aoa_to_sheet(data);
    XLSX.utils.book_append_sheet(wb, ws, "题-单元映射");
    XLSX.writeFile(wb, "cams_question_unit_matrix.xlsx");
  }

  /**
   * 渲染整个映射表页面
   */
  function render(state) {
    // 构建数据索引
    var matrix = buildMatrix(state);
    // 收集所有出现过的单元ID
    var allUnitIds = {};
    Object.keys(matrix).forEach(function (qid) {
      matrix[qid].forEach(function (item) { allUnitIds[item.unit_id] = true; });
    });
    // 按 state.units 中的顺序排序，只保留有映射关系的单元
    var orderedUnits = (state.units || []).filter(function (u) { return allUnitIds[u.unit_id]; });

    // 构造页面 DOM
    var page = document.createElement("div");
    page.id = "matrixPage";
    page.className = "matrix-page";
    page.innerHTML =
      '<header class="matrix-header">' +
        '<button class="matrix-back" data-home>&larr; 返回工作台</button>' +
        '<h2>题-单元映射表</h2>' +
        '<button class="matrix-export" id="matrixExport">导出 Excel</button>' +
      "</header>" +
      '<div class="matrix-toolbar">' +
        '<input type="search" id="matrixSearch" placeholder="搜索题目ID或题干...">' +
        '<select id="matrixUnitFilter"><option value="">全部单元</option>' + renderUnitOptions(orderedUnits) + "</select>" +
        '<select id="matrixStrengthFilter"><option value="">全部强度</option><option value="direct">直接支持</option><option value="indirect">间接支持</option><option value="context">上下文关联</option></select>' +
      "</div>" +
      '<div class="matrix-table-wrap">' +
        '<table class="matrix-table">' +
          "<thead>" +
            "<tr>" +
              '<th class="col-id">题目ID</th>' +
              '<th class="col-stem">题干</th>' +
              '<th class="col-units">涉及 Unit/CP</th>' +
            "</tr>" +
          "</thead>" +
          '<tbody id="matrixBody"></tbody>' +
        "</table>" +
      "</div>" +
      '<div class="matrix-footer">' +
        '<span class="matrix-count" id="matrixCount">共 0 题</span>' +
      "</div>";

    document.body.appendChild(page);

    // 缓存 DOM 引用
    var tbody = document.getElementById("matrixBody");
    var countEl = document.getElementById("matrixCount");
    var searchInput = document.getElementById("matrixSearch");
    var unitFilter = document.getElementById("matrixUnitFilter");
    var strengthFilter = document.getElementById("matrixStrengthFilter");

    // 构建 unitId -> unit 的快速查找表
    var unitMap = {};
    (state.units || []).forEach(function (u) { unitMap[u.unit_id] = u; });

    /**
     * 应用筛选并刷新表格
     */
    function applyFilter() {
      var filtered = filterRows(
        state.questions || [],
        matrix,
        searchInput.value,
        unitFilter.value,
        strengthFilter.value
      );
      tbody.innerHTML = renderRows(filtered, matrix, unitMap);
      countEl.textContent = "共 " + filtered.length + " 题";
    }

    // 初始渲染
    applyFilter();

    // 绑定筛选事件（使用 input 事件实时搜索）
    searchInput.addEventListener("input", applyFilter);
    unitFilter.addEventListener("change", applyFilter);
    strengthFilter.addEventListener("change", applyFilter);

    // 行点击跳转
    tbody.addEventListener("click", function (e) {
      var tr = e.target.closest("tr");
      if (!tr) return;
      var qid = tr.getAttribute("data-question-id");
      if (qid && window.CamsApp && window.CamsApp.selectQuestion) {
        window.CamsApp.selectQuestion(qid);
      }
    });

    // 导出按钮
    document.getElementById("matrixExport").addEventListener("click", function () {
      // 导出时使用当前筛选后的数据
      var filtered = filterRows(
        state.questions || [],
        matrix,
        searchInput.value,
        unitFilter.value,
        strengthFilter.value
      );
      exportExcel(state, filtered, matrix);
    });

    // 保存引用供 destroy 清理
    page._handlers = {
      searchInput: searchInput,
      unitFilter: unitFilter,
      strengthFilter: strengthFilter,
      tbody: tbody,
      exportBtn: document.getElementById("matrixExport")
    };
  }

  /**
   * 清理事件监听和 DOM
   */
  function destroy() {
    var page = document.getElementById("matrixPage");
    if (!page) return;
    var h = page._handlers;
    if (h) {
      // 移除事件监听（通过替换节点来彻底清理）
      // 但 input/change 事件没有直接 remove 的必要，因为 DOM 会被移除
    }
    page.remove();
  }

  window.CamsMatrix = {
    render: render,
    destroy: destroy
  };
})();