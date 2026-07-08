# CAMS 教研工作台 — 前端

## 技术栈

纯静态页面，无框架。HTML + CSS + 原生 JS（IIFE 模块），通过 `window.CamsXxx` 全局对象通信。数据来自 `data/` 目录下的 JSON 文件，运行时通过 `fetch` 加载。

## 加载顺序

JS 按依赖关系排列，后面的依赖前面的全局对象：

```
utils.js  →  store.js  →  reader.js  →  panel.js  →  feedback.js  →  search.js  →  app.js
```

`app.js` 是唯一入口，在 `DOMContentLoaded` 时调用 `CamsStore.load()` 加载所有数据，然后初始化各个模块。

## 文件清单

### index.html

应用入口页面。三栏布局：左侧目录（toc-pane）、中间教材阅读区（reader-pane）、右侧详情面板（detail-pane）。顶部工具栏含工作模式切换（看书备课 / 新题解析 / 学生答疑）和搜索框。

### css/workbench.css

全局样式。覆盖三栏布局、教材阅读、考点标注、搜索面板、新题解析和学生答疑表单。

### js/utils.js

工具函数库，挂载到 `window.CamsUtils`：
- DOM 操作辅助（byId、escapeHtml、createElement 等）
- 字符串处理、数组去重、节流
- 教材原文格式化

### js/store.js

数据加载与内存索引层，挂载到 `window.CamsStore`：
- `load()` — 从 `data/` 加载全部 JSON 并构建查询索引
- 构建的索引：`cardById`、`questionById`、`qaById`、`cardToQuestions`、`cardToSection`、`sectionToCards`、`paragraphByCard`、`examPointById`、`examPointByCardId`、`optionEvidenceByQuestionId` 等
- 对外暴露查询方法：`getCardsForSection`、`getExamPointsForCard`、`getOptionEvidenceForQuestion` 等

详见下方的「数据资产」章节。

### js/reader.js

教材阅读区渲染，挂载到 `window.CamsReader`：
- `render()` — 渲染全部教材章节段落，注入句卡高亮和考点标注
- `scrollToCard()` — 滚动定位到指定句卡对应的段落
- `scrollToParagraph()` — 滚动定位到段落
- 章节展开/折叠、阅读进度

### js/panel.js

右侧详情面板渲染，挂载到 `window.CamsPanel`：
- `renderWorkbenchHome()` — 工作台首页（三种工作模式各自的入口）
- `renderQuestionDetail()` — 题目详情页
- `renderQaDetail()` — 答疑详情页
- `renderExamPointDetail()` — 考点详情页
- `renderQuestionList()` — 题目列表
- `renderExamPointList()` — 考点列表
- `renderGraphModal()` — 知识图谱弹窗

### js/feedback.js

教研反馈收集，挂载到 `window.CamsFeedback`：
- `add()` — 添加反馈条目（考点确认/驳回/改名/合并/拆分、选项证据审核）
- `exportJSON()` — 导出反馈为 JSON 下载
- `count()`、`clear()` — 计数、清空

### js/search.js

全文搜索，挂载到 `window.CamsSearch`：
- `bind()` — 绑定搜索输入框和结果面板
- 搜索范围：教材原文、题目题干、答疑内容

### js/app.js

应用主入口，挂载到 `window.CamsApp`：
- `init()` — 初始化数据加载和各模块
- 视图路由：`navigateTo()` 切换 home/card/question/qa/examPoint/questionList/examPointList
- 工作模式切换：`setWorkMode()` 切换 read/explain/qa
- 新题解析流程：调用 `127.0.0.1:8765` API
- 学生答疑流程：调用 `127.0.0.1:8766` API
- 历史记录：前进/后退栈管理
- 目录折叠状态持久化到 localStorage

## 数据资产

前端运行时通过 `store.js` 加载 `data/` 下的 11 个 JSON 文件。按生成方式分为三层：

### 原始事实层（`data/source/`）

不由 pipeline 生成，从外部来源一次性提取，只读不写。

**1. cards_v6_sentence.json** — 全书句卡池

每张句卡是一段教材原文的最小证据单元，约 5199 张。字段：`card_id`（`v6s_N#####` 格式）、`knowledge`、`citation`、`chapter_path`、`page`、`sentence_index`。

前端构建 `cardById` 索引，是所有教材原文追溯的最终依据。阅读区句卡高亮、考点详情引用的教材原文、选项证据的 `quote` 字段，最终都通过 `card_id` 回到这个文件。

**2. questions.json** — 正式题库

全教材 2-6 章约 720 道正式题目。字段：`id`（如 `3.1_1`）、`section`、`stem`、`options`（`{A, B, C, D}`）、`answer`、`explanation`。

题干和答案视为可信事实。解析（`explanation`）由教研提供，可作为参考线索但不能替代教材句卡依据。

**3. qa.json** — 学生答疑记录

正式导入的学生答疑。字段：`id`、`question`（学生原问）、`answer`（老师回复）、`source_file`。

前端将其作为易错信号来源，展示答疑原文并关联到题目和考点。答疑不直接生成考点。

---

### Pipeline 产物（`data/derived/`）

以下文件由 `pipeline/` 脚本生成，可随时重跑。

**4. chapters/v6_full.json** — 教材阅读页结构

```
sections[] → subsections[] → paragraphs[] → { text, card_ids[], highlight_card_ids[] }
```

教材原文按章节→小节→段落的树形结构。`reader.js` 据此渲染中间阅读区，`card_ids` 决定哪些句卡落在哪个段落，用于点击定位和滚动。

**5. option_evidence_map.json** — 选项级教材证据（核心枢纽）

```
items[] → { question_id, options[] → { option, judgement, evidence_cards[], explanation, common_trap } }
```

记录每道题每个选项的教材依据：该选项为什么对/错，引用了哪些教材句卡，解析文本，易错提示。`evidence_cards[]` 中的 `card_id` 必须能回到 `cards_v6_sentence.json`。

前端展示题目详情时读取此文件，也是下游 `exam_points.json` 生成的核心输入。

**6. question_card_map.json** — 题目到句卡的粗映射（待废弃）

```
mappings: { "3.1_1": { knowledge_point, matched_card_ids[], match_method } }
```

题目级别的句卡关联，粒度比 `option_evidence_map.json` 粗。前端用于构建 `cardToQuestions` 反向索引：在阅读区点击一句卡时，查出它关联了哪些题目。

⚠️ **此文件是冗余资产**：其 `matched_card_ids` 完全可由 `option_evidence_map.json` 聚合得到（遍历各选项的 `evidence_cards[].card_id`，按 `question_id` 去重即可）。保留它只是因为前端 `store.js` 的 `buildQuestionIndexes()` 尚未改从 `optionEvidence` 聚合。计划后续在前端改掉后废弃此文件。

**7. exam_points.json** — 正式考点

```
exam_points[] → { id, title, source_card_ids[], question_ids[], qa_ids[], is_high_frequency, teaching_object_kind }
```

合并后的正式考点资产。前端展示考点列表、考点详情、高频标记。通过 `examPointByCardId` 索引，用户点击句卡可看到该句卡属于哪些考点。

**8. sentence_exam_point_map.json** — 句卡到考点的段落级映射（待废弃）

```
paragraphs[] → { paragraph_id, exam_point_ids[] }
```

将考点关联到教材阅读页的具体段落。原计划前端据此在段落旁渲染考点标注标签。

⚠️ **此文件是冗余资产**：前端实际只用了 `stats.paragraphs_with_exam_points` 一个计数，`paragraphs[]` 和 `sentences[]` 数组从未被渲染函数使用。段落考点标注已通过 `examPointByCardId` 索引（从 `exam_points.json` 构建）实现，不依赖此文件。首页计数也可从 `exam_points.json` 直接派生。计划废弃。

**9. qa_bindings.json** — 答疑到题目的绑定（需重建）

```
bindings[] → { qa_id, bound_question_id, match_method, match_score, inherited_card_ids[] }
```

通过文本匹配将答疑记录绑定到正式题库中的题目，继承题目的句卡证据。前端从答疑详情可跳转到关联题目。

⚠️ **需重建**：当前仅覆盖第 2 章 37 条。`inherited_card_ids` 从 `question_card_map.json` 抄来，该文件废弃后需改为从 `option_evidence_map.json` 聚合句卡。生成脚本为旧 `data_pipeline/bind_qa.py`。

**10. kg_data.json** — 知识图谱 ✅

```
v6s_N#####: { section, edges[] }
_edges: [{ from, to, type, detail }] (633条)
```

3719 个 v6s 句卡节点，633 条概念关系边（包含、并列、导致、缓解、前提、依据）。前端构建三个索引：
- `cardToSection`：每张句卡归属到教材概念，点击句卡时显示"所属知识点"
- `sectionToCards`：每个概念下有哪些句卡
- `sectionEdges`：概念间关系，供详情面板图谱弹窗使用

生成脚本：`tools/知识图谱/`。未覆盖的句卡由 `attachFallbackSections` 从教材结构自动补充概念归属。

---

### 页码映射（`data/page_maps/`）

**11. card_page_map_v6.json** — 句卡到教材页码

```
cards: { "v6s_N#####": { page_number, pdf_page }, ... }
```

每张句卡在教材 PDF 中的页码。前端展示句卡时标注页码，方便对照教材原文。

---

### 依赖关系图

```
cards_v6_sentence ──────────────────────┐  ✅
questions ──────────────────────────────┤  ✅
qa ─────────────────────────────────────┤  ✅
chapters/v6_full ──── 决定阅读区渲染 ────┤  ✅
                                         │
option_evidence_map ── 核心证据枢纽 ─────┤  ⚠️ 44/718 题
question_card_map ──── 题目↔句卡粗链 ───┤  待废弃
exam_points ────────── 考点资产 ────────┤  ❌ 缺
sentence_exam_point_map ─ 段落↔考点 ────┤  待废弃
qa_bindings ────────── 答疑↔题目绑定 ───┤  ✅ (69条)
kg_data ────────────── 概念图谱 ────────┤  ✅ (3719节点)
card_page_map_v6 ───── 页码映射 ────────┘  ✅
```

三层物理隔离：
- `cards/` — 句卡池，全系统唯一教材依据
- `source/` — 原始事实，不从 pipeline 生成（questions、qa）
- `derived/` — pipeline 产物，可随时重跑（chapters、option_evidence、qa_bindings、exam_points、kg_data 等）

---

## 外部依赖

| 依赖 | 地址 | 说明 |
|---|---|---|
| 数据文件 | `../data/` | 上述 11 个 JSON 静态资产 |
| 新题解析 API | `http://127.0.0.1:8765/api/new-question/` | 实时新题解析服务 |
| 学生答疑 API | `http://127.0.0.1:8766/api/student-qa/` | 实时学生答疑服务 |
