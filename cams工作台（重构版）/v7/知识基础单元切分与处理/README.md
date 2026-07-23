# v7 知识基础单元切分与处理设计

本目录用于定义 CAMS v7 的“知识基础单元”切分、处理中英对齐、摘要与术语字段生成。它是后续题目证据生成和知识图谱提取的前置环节，但本目录本身不负责生成考点图谱。

边界说明：

- 本环节产出：可冻结的 v7 双语知识基础单元 `unit_id`。
- 后续环节产出：题目-选项-知识单元证据边、考点聚合、父子/并列关系和知识图谱。
- 因此“知识图谱提取”应作为独立目录或独立 Phase，不与本目录混用。

## 当前输入

已完成的 v7 基础产物：

- 中文拆分 PDF：`../work/sources/v7_zh_split.pdf`
- 英文拆分 PDF：`../work/sources/v7_en_split.pdf`
- 页码映射：`../work/sources/v7_split_page_map.json`
- 页级中英对齐文本：`../work/sources/v7_page_aligned_text.json`
- MinerU block 页码回填：`../work/sources/v7_mineru_block_page_matches.json`
- MinerU 质量报告：`../work/audit/v7_mineru_quality_report.md`
- 中文 MinerU 合并版：`D:\守正公司工作区\cams考试\教材、答疑记录、习题与参考文献\教材原文\v7\mineru提取\中文\v7_zh_mineru_merged.md`
- 英文 MinerU 合并版：`D:\守正公司工作区\cams考试\教材、答疑记录、习题与参考文献\教材原文\v7\mineru提取\英文\v7_en_mineru_merged.md`

来源准备脚本：

- `scripts/build_split_bilingual_pdf.py`：从 v7 中英对照 PDF 生成中/英文拆分 PDF 和页码映射。
- `scripts/prepare_mineru_phase0.py`：合并 MinerU markdown，生成页级对齐文本、block 页码回填和质量报告。

已知质量结论：

- MinerU markdown 已中英分离，但没有原生页码标记。
- 页码必须来自拆分 PDF 文本层匹配。
- 英文 block 可用页码回填率约 99.95%，中文 block 可用页码回填率约 99.93%。
- 英文应作为知识单元切分锚点，中文作为展示、复核和中文检索摘要来源。

## 总体原则

### 1. 英文主切分，中文主展示

v7 的概念源头以英文为准。知识单元的边界、原文依据、句子 span 首先从英文 MinerU 结构和英文 PDF 页码中确定。

中文不负责主切分。中文用于：

- 前端默认展示摘要。
- 教研人工复核。
- 中文题目检索的摘要和术语补强。
- 翻译不一致时辅助定位。

### 2. 单层正式绑定对象

正式绑定对象只有 `unit_id`。不建立独立 sentence 层、paragraph 层或 block 层。

sentence、block、heading、table row 都可以作为构建 `unit_id` 的来源和审计依据，但题目证据、考点聚合、父子关系和前端展示最终都必须回到 `unit_id`。

### 3. 可复现性的准确定义

不能宣称 LLM 语义切分天然可复现。v7 采用以下口径：

```text
规则层可复现：
- MinerU block 顺序
- 英文拆句结果
- block/page 映射
- span 起止位置
- unit 物化逻辑

LLM 层不可保证数学复现：
- 散文句子分组
- 标题是否可考
- 多断言判断
- knowledge_zh / knowledge_en 摘要

工程保障：
- 固定 model_id
- 固定 prompt_version
- temperature=0
- 固定 JSON schema
- 保存 input_hash、prompt_hash、model_id、raw_response
- 生成 decision_manifest
- 正式构建默认 replay decision_manifest，不重新问 LLM
```

因此，正式说法是：**已冻结的 decision_manifest 可以 100% 回放；如果换模型、换 prompt 或清缓存，就是新版本重切。**

### 4. unit_id 生命周期

知识单元在冻结前只能使用临时编号：

```text
v7u_tmp_N000001  草稿阶段 unit，不允许下游题目绑定
v7u_N000001      验收冻结后的正式 unit，允许进入题目证据绑定
```

抽样验收前，不允许任何下游模块依赖 `v7u_tmp_*` 进行正式题目绑定。重切时不能覆盖已经冻结的 `v7u_N*`，只能新建版本或标记 deprecated。

### 5. 不做深树

图谱结构最大深度为 2：

```text
parent -> leaf
```

允许：

- `topic_parent -> leaf`
- `list_parent -> leaf`

不允许：

- `topic_parent -> list_parent -> list_item`

如果同一标题下既有分类列表又有定义、风险、义务等内容，它们共享 `heading_context`，但不做三层嵌套。

## 切分策略

### 1. 不是纯规则切分

“一个 unit 只表达一个可被题目引用的教材知识点”本身是语义标准。散文段落里的主题切换、事实点边界、多断言判断，不能靠正则稳定完成。

因此第一版采用：

```text
规则负责结构定位、拆句、页码、span 和物化。
LLM 负责散文句子分组、标题角色判断和摘要生成。
人工抽样负责冻结前验收。
```

### 2. 规则层负责什么

规则层处理确定性结构：

- 读取英文 MinerU block。
- 合并 block 页码回填结果。
- 建立 heading stack。
- 识别 heading、paragraph、list item、table、table row。
- 过滤封面、目录、致谢、版权、人员名单等非知识正文。
- 对英文 paragraph 做稳定拆句。
- 对列表保留总述句和每个列表项的来源 span。
- 对表格先分类为内容表或非内容表，只有内容表进入候选。
- 记录 `pdf_page`、`printed_page`、`source_block_id`、`char_start/char_end`。

### 3. LLM 层负责什么

LLM 只在候选局部内裁判，不允许脱离原文自由发明。

LLM 的输入窗口必须受控，不能一次看整页，也不能一句一句孤立判断。第一版窗口规则：

```text
普通散文 paragraph：一次看 3-8 句。
短 paragraph：直接全段。
长 paragraph：按 6 句滑窗，前后重叠 1 句。
列表：不走散文分组，按 list_parent + list_item 规则处理。
表格：不走散文分组，先识别内容表，再按行处理。
案例：按自然段或 5-8 句窗口处理。
```

窗口冲突处理：

- 如果两个滑窗对同一句的归属判断冲突，标记 `sentence_group_conflict`。
- 冲突样本进入 `needs_review`，不强行自动定稿。
- LLM 只能输出句子编号分组，不能直接输出 `en_quote`。

散文 paragraph 输入：

```json
{
  "block_id": "v7en_b000447",
  "heading_stack": ["Politically exposed person risks"],
  "sentences": [
    {"sid": 1, "text": "A politically exposed person ..."},
    {"sid": 2, "text": "One challenge in identifying PEPs ..."}
  ]
}
```

LLM 输出必须是句子编号分组：

```json
{
  "sentence_groups": [
    {
      "sentence_ids": [1],
      "unit_type": "definition",
      "knowledge_hint_en": "PEP definition",
      "reason": "This sentence defines PEP."
    },
    {
      "sentence_ids": [2],
      "unit_type": "risk_indicator",
      "knowledge_hint_en": "PEP identification challenge",
      "reason": "This sentence states a challenge in identifying PEPs."
    }
  ],
  "risk_flags": []
}
```

LLM 不输出新的依据原文。`en_quote` 只能由 `sentence_ids` 回填原文 span 得到。

### 4. 散文段落必须切

连续散文段落里只要出现多个独立知识断言，就应切分。不能因为没有连接词就整段作为一个 unit。

例如 PEP 段落：

```text
A politically exposed person (PEP) is an individual...
One challenge in identifying PEPs is the varying guidance...
```

应切为：

- PEP 定义。
- PEP 识别难点。

这一步必须依赖 LLM 语义分组，但分组结果要通过 decision_manifest 固化。

## parent 节点规则

### 1. topic_parent

`topic_parent` 只作为结构和召回扩展节点，不作为直接证据。

它没有拼装 quote：

```json
{
  "unit_type": "topic_parent",
  "evidence_status": "heading_only",
  "en_quote": null,
  "heading_text": "Politically exposed person risks",
  "children": ["v7u_tmp_N000101", "v7u_tmp_N000102"],
  "can_be_direct_evidence": false,
  "retrieval_weight": "low"
}
```

禁止把 `heading + 下方说明句` 拼成 quote。拼装 quote 不是教材连续原文，不能作为正式依据。

`topic_parent` 不是 H2 标题下所有 leaf 的自动桶。只有当若干 leaf 属于同一个明确主题簇时，才生成 `topic_parent`。如果一个 H2 下同时包含定义、分类列表、风险表现、规则义务等多个主题簇，应拆成多个 parent，或只保留 `heading_context` 而不生成 `topic_parent`。

### 2. list_parent

如果原文存在明确列表总述句，`list_parent` 可以使用该总述句作为 `en_quote`。

例如：

```text
According to FATF, there are three types of PEPs:
```

可以物化为：

```json
{
  "unit_type": "list_parent",
  "evidence_status": "direct",
  "en_quote": "According to FATF, there are three types of PEPs:",
  "children": ["foreign_pep_unit", "domestic_pep_unit", "io_pep_unit"],
  "can_be_direct_evidence": true
}
```

如果没有原文总述句，只有标题，则只能降级为 `heading_only`。

`list_parent` 与 `topic_parent` 平级共存，不互相嵌套。二者可以共享同一个 `heading_context`，但 `topic_parent.children` 不包含 `list_parent`，也不包含该 `list_parent` 下的 list item。这样保证结构深度不超过 2。

### 3. 题目绑定优先落叶子

题目证据优先绑定到 leaf unit。父节点只能用于：

- 结构展示。
- 召回扩展。
- 帮助解释多个 leaf 的共同主题。

`heading_only` 父节点不能产生 `direct_single` 证据。

## 英文检索切片

英文侧必须保留句级检索切片，避免 `en_quote` 过长导致召回稀释。

`en_quote` 是 unit 级英文证据，用于展示和复核。`en_sentences[]` 是检索切片，用于 BM25 和向量召回，命中后回映射到所属 `unit_id`。

```json
{
  "en_quote": "A politically exposed person (PEP) is an individual in a prominent political function...",
  "en_sentences": [
    {
      "sentence_id": "v7en_b000447_s001",
      "text": "A politically exposed person (PEP) is an individual in a prominent political function...",
      "role": "retrieval_slice",
      "parent_unit_id": "v7u_tmp_N000001"
    }
  ]
}
```

英文索引规则：

- BM25 索引：`en_sentences[].text + knowledge_en + terms.en`。
- 向量索引：优先索引 `en_sentences[].text`。
- 命中 sentence 后返回 `parent_unit_id`。
- `en_quote` 不作为唯一向量粒度。

## 中文字段与检索规则

### 1. 第一版不做英中句内子串对齐

英文 unit 越细，中文子串对齐越难。中文 MinerU 中存在无断句或断句不可靠的段落，第一版不承诺稳定生成“对齐英文 unit 的中文子串”。

因此第一版中文字段定义为：

```json
{
  "zh_context_full": "同页或同段完整中文，仅供展开复核",
  "zh_display_text": "默认等于 knowledge_zh，用于前端摘要展示",
  "zh_display_mode": "generated_summary|aligned_subspan|context_only",
  "knowledge_zh": "一句话中文知识摘要",
  "zh_search_text": null,
  "zh_search_text_status": "not_available|available",
  "risk_flags": ["zh_subspan_unavailable"]
}
```

只有在中文来源天然可对齐时，才允许填充 `zh_search_text`：

```text
- 中文本身是列表项，能和英文 list_item 一一对应。
- 中文本身是表格行，能和英文 table_row 一一对应。
- 中文 block 有明确句号/分号，且规则切分后能稳定匹配英文 unit。
```

不允许默认填充 `zh_search_text` 的情况：

```text
- 中文是无断句长段。
- 需要句内子串对齐。
- 需要 LLM 判断中文片段边界。
```

因此第一版多数 unit 的 `zh_search_text` 应为 `null`，而不是等于 `knowledge_zh`。`zh_search_text` 是预留字段，不是第一版默认能力。

### 2. 中文主索引

第一版中文检索只索引：

- `knowledge_zh`
- `terms[].zh`
- `zh_search_text_status=available` 时的 `zh_search_text`

不索引：

- 大段 `zh_context_full`
- `context_before/after`

原因：如果把整段中文原文放进向量索引，会重演 v6 句卡过宽导致的噪声召回问题。

### 3. knowledge_zh 是关键字段

因为 `zh_search_text` 第一版多数不可用，所以 `knowledge_zh` 不是装饰字段，而是中文召回核心字段。必须重点抽审：

- 是否准确概括英文 unit。
- 是否保留教材核心术语。
- 是否没有混入相邻上下文知识点。
- 是否能覆盖中文题目的常见表达。

`knowledge_zh` 必须基于精确 `en_quote` 生成，而不是基于整段中文机翻文本生成。推荐输入：

```json
{
  "en_quote": "精确英文 unit 原文",
  "heading_context": ["当前标题路径"],
  "terms_map": {
    "politically exposed person": "政治公众人物",
    "money laundering": "洗钱"
  },
  "constraints": [
    "不得引入 en_quote 之外的信息",
    "不得改写概念边界",
    "必须优先使用 terms_map 中的中文术语"
  ]
}
```

推荐输出：

```json
{
  "knowledge_zh": "20-40字中文摘要，保留核心术语",
  "knowledge_en": "one-sentence English summary",
  "terms_used": ["politically exposed person", "政治公众人物"],
  "confidence": "high|medium|low",
  "risk_flags": []
}
```

如果术语未命中、摘要混入上下文、或摘要不能忠实表达 `en_quote`，标记 `knowledge_needs_review`。

### 4. 教研展示口径

前端和报告不能把 LLM 生成的中文摘要写成“中文原文依据”。第一版建议展示为：

```text
知识点摘要：
PEP 识别难点在于各司法辖区的指引和建议存在差异。

英文原文依据：
One challenge in identifying PEPs is the varying guidance...

教材页码：
英文教材 P57 / 中文教材 P57

中文上下文：
[展开查看]
完整中文段落……
```

字段对应：

```json
{
  "knowledge_zh": "知识点摘要",
  "zh_display_text": "默认等于 knowledge_zh",
  "zh_display_mode": "generated_summary",
  "en_quote": "英文原文依据",
  "printed_page": "57",
  "zh_context_full": "中文上下文"
}
```

证据精确性以 `en_quote + printed_page` 为准；中文完整段落只做展开复核。

### 4. terms.zh 是检索兜底

术语表同样是核心检索资产，不只是展示美化。第一批术语至少覆盖：

- PEP / politically exposed person / 政治公众人物 / 政治敏感人物
- BO / beneficial owner / 受益所有人
- UBO / ultimate beneficial owner / 最终受益所有人
- ML / money laundering / 洗钱
- MSB / money services business / 货币服务企业
- AFC / anti-financial crime / 金融犯罪防控
- AML / anti-money laundering / 反洗钱
- CFT / countering the financing of terrorism / 反恐怖融资
- sanctions / 制裁
- shell company / 壳公司
- shelf company / 现成公司

## 第一版产物

### 1. block 标准化

```text
work/base_units/
├── v7_en_blocks.json
├── v7_zh_blocks.json
└── block_normalization_report.md
```

block 示例：

```json
{
  "block_id": "v7en_b000447",
  "lang": "en",
  "block_type": "paragraph",
  "text": "A politically exposed person...",
  "pdf_page": 62,
  "printed_page": "57",
  "heading_stack": ["Politically exposed person risks"],
  "source_file": "v7_en_mineru_merged.md",
  "source_block_index": 447
}
```

### 2. LLM decision manifest

```text
work/base_units/
├── llm_decisions/
│   ├── prose_sentence_groups.jsonl
│   ├── heading_roles.jsonl
│   └── knowledge_summaries.jsonl
└── llm_decision_manifest.json
```

manifest 必须记录：

```json
{
  "prompt_version": "v7_unit_split_v1",
  "model_id": "model-name",
  "temperature": 0,
  "input_hash": "...",
  "prompt_hash": "...",
  "raw_response_path": "...",
  "parsed_response": {},
  "status": "passed|malformed|needs_review"
}
```

### 3. 草稿知识单元

```text
work/base_units/v7_units_draft.json
```

草稿 unit 使用 `v7u_tmp_N*`。

小样本调试阶段允许生成独立产物：

```text
work/base_units/draft/
├── v7_units_draft.sample.json
├── v7_units_draft.sample.enriched.json
├── v7_units_draft.sample.audit.json
├── v7_units_draft.stratified_rule.json
├── v7_units_draft.stratified_llm.json
├── v7_units_draft.stratified_table.json
├── v7_units_draft.stratified_combined.json
└── v7_units_draft.pilot_<chapter_slug>.llm.json
```

该产物只能用于抽审知识单元切分质量，不允许进入正式题目绑定。

### 3.1 分层样本工程规则

分层样本用于验证全书批处理前的三类核心结构：

1. **规则可直接物化的结构**
   - `list_parent`：原文存在明确列表总述句，可作为 direct。
   - `list_item`：每条列表项可作为 direct。
   - 例：欺诈红旗、电商红旗、加密资产红旗列表项。

2. **必须阻断的结构**
   - `process_context`：只表示定位到流程相关段落，不是叶子知识单元。
   - `paragraph_needs_llm`：散文段落必须经句子分组后才可 direct。
   - `table_needs_parser`：HTML 表格必须经表格解析后才可 direct。
   - 阻断候选的 `can_be_direct_evidence=false`，`evidence_status=needs_llm|needs_parser`。

3. **LLM 句子分组后的叶子单元**
   - LLM 只输出 `sentence_ids` 分组、`unit_type`、`knowledge_hint_en` 和理由。
   - `en_quote` 由脚本按 `sentence_ids` 从原文回填，不允许 LLM 发明。
   - 第一版质量门：单个 LLM group 超过 3 句时降级为 `needs_review`，不直接作为证据。

4. **表格解析后的叶子单元**
   - 第一版只处理有表头的内容表，过滤致谢、版权、目录、人员名单等非知识表。
   - 表格单元按“列标题 + 行标题 + 单元格文本”形成 `table_cell` direct unit。
   - 例：`MSB — Regulation: ...`、`Hawala — Transparency: ...`。

当前样本组合产物：

```text
work/base_units/draft/v7_units_draft.stratified_combined.json
```

其中：
- `items`：只放通过审计的 direct 草稿单元。
- `review_items`：放 LLM 生成但需人工或规则复核的非 direct 单元。
- `blocked_source_candidates`：保留原始阻断段落/表格与派生 direct 单元之间的追踪关系。

### 4. 冻结知识单元

```text
work/units/
├── v7_bilingual_units.json
├── v7_units_as_cards.json
├── unit_freeze_manifest.json
└── unit_build_report.md
```

冻结后才允许题目证据绑定使用。

## schema 草案

### leaf unit

```json
{
  "unit_id": "v7u_tmp_N000001",
  "unit_status": "draft|frozen|deprecated",
  "unit_type": "definition|classification|rule|obligation|process|red_flag|risk_indicator|case_fact|example|list_item|table_row|fact",
  "type": "definition|classification|process|fact|case|rule|risk_indicator|context",
  "evidence_status": "direct",
  "can_be_direct_evidence": true,
  "en_quote": "English source text reconstructed from sentence spans.",
  "en_sentence_ids": ["v7en_b000447_s001"],
  "en_sentences": [
    {
      "sentence_id": "v7en_b000447_s001",
      "text": "English sentence slice.",
      "role": "retrieval_slice",
      "parent_unit_id": "v7u_tmp_N000001"
    }
  ],
  "zh_context_full": "同页或同段完整中文，仅供展开复核。",
  "zh_display_text": "默认等于 knowledge_zh，用于前端摘要展示。",
  "zh_display_mode": "generated_summary",
  "knowledge_en": "one-sentence English summary",
  "knowledge_zh": "一句话中文知识摘要",
  "zh_search_text": null,
  "zh_search_text_status": "not_available",
  "terms": [
    {"en": "politically exposed person", "zh": "政治公众人物", "source": "term_map|llm|manual"}
  ],
  "pdf_page": 62,
  "printed_page": "57",
  "page_span": [62],
  "heading_context": ["Politically exposed person risks"],
  "source": {
    "en_block_id": "v7en_b000447",
    "zh_block_ids": ["v7zh_b000420"],
    "decision_ids": ["decision_000001"]
  },
  "risk_flags": ["zh_subspan_unavailable"]
}
```

### heading_only parent

```json
{
  "unit_id": "v7u_tmp_N000100",
  "unit_status": "draft|frozen|deprecated",
  "unit_type": "topic_parent",
  "evidence_status": "heading_only",
  "can_be_direct_evidence": false,
  "en_quote": null,
  "heading_text": "Politically exposed person risks",
  "children": ["v7u_tmp_N000101", "v7u_tmp_N000102"],
  "pdf_page": 62,
  "printed_page": "57",
  "retrieval_weight": "low",
  "risk_flags": []
}
```

## 质量门

第一版不直接全量进下游。验收分两层：链路样本用于验证流程能跑通，分层质量样本用于验证各类知识单元的切分质量。

### 1. 链路样本

- PEP：PDF 62-63，教材页 57-58。
- BO/UBO：PDF 64-65，教材页 59-60。
- APAC 案例 / AFC regulations：PDF 183-185，教材页 178-180。

这些样本只用于验证端到端流程，不足以证明全书质量。

### 2. 分层质量样本

每种 unit_type 至少抽样，数量根据实际产出调整，建议每类 10-20 个：

- `definition`
- `classification`
- `rule`
- `obligation`
- `process`
- `red_flag`
- `risk_indicator`
- `case_fact`
- `table_row`
- `list_parent`
- `list_item`

检查项：

- 英文 unit 是否一知识点一单元。
- 散文段落是否被合理切分，而不是整段塞入。
- 是否存在该切未切、过度切分或类型误判。
- `topic_parent` 是否只有 heading，不拼装 quote。
- `topic_parent` 是否变成 H2 下所有 leaf 的大桶。
- `list_parent` 与 `topic_parent` 是否平级共存，没有形成三层树。
- 树深度是否不超过 2。
- 中文是否没有进入大段向量索引。
- `zh_display_text` 是否是摘要或可靠子串，没有把整段中文冒充精确证据。
- `zh_search_text` 是否只在天然可对齐时填充。
- `knowledge_zh` 是否能支撑中文召回。
- 术语是否覆盖关键英文/中文表达。
- `v7u_tmp_*` 是否未进入下游绑定。

## 后续优先级

已完成到样本验证和全书路由 dry-run：

1. block 标准化和过滤：已完成，产物位于 `work/base_units/`。
2. 英文拆句：已完成，句子只作为检索切片和 LLM 分组输入。
3. 样本级 prose LLM sentence grouping：已跑通，LLM 只输出 `sentence_ids`。
4. 样本级 `list_parent/list_item/leaf/table_cell` 物化：已跑通。
5. 样本级 `knowledge_zh` 与 terms 回填：已跑通，但仍是 deterministic sample v1，不是正式生成策略。
6. 分层样本审计：当前 sample/rule/LLM/table 四类审计均为 0 issue。
7. 全书路由 dry-run：已完成，不调用 LLM，不生成正式 unit。
8. 章节级 LLM pilot：已用 `Money Laundering and Financial Crime` 跑通一轮。
   - 输入：`work/base_units/llm_batches/money-laundering-and-financial-crime.jsonl`
   - 决策：`work/base_units/llm_batches/pilot_money_laundering_and_financial_crime_decisions.subagent.jsonl`
   - 物化：`work/base_units/draft/v7_units_draft.pilot_money_laundering_and_financial_crime.llm.json`
   - 报告：`work/base_units/draft/v7_units_draft.pilot_money_laundering_and_financial_crime.llm_report.md`
   - 审计：`work/base_units/draft/v7_units_draft.pilot_money_laundering_and_financial_crime.llm_audit.json`
   - 结果：35 个请求、55 个分组、52 个 direct unit、3 个 review item、审计 0 issue。
   - 典型 direct：洗钱定义、上游犯罪定义与例子、三阶段、处置/离析/融合阶段、案例红旗。
   - 典型 review：导论学习目标、跨页残句。
   - 限制：该 pilot 只物化 LLM sentence grouping 结果，尚未生成正式 `knowledge_zh`。
9. 章节级 combined pilot：已将同章节 LLM pilot 与规则直出 list 产物合并。
   - 脚本：`知识基础单元切分与处理/scripts/build_chapter_combined_pilot_units.py`
   - 产物：`work/base_units/draft/v7_units_draft.pilot_money_laundering_and_financial_crime.combined.json`
   - 报告：`work/base_units/draft/v7_units_draft.pilot_money_laundering_and_financial_crime.combined_report.md`
   - 审计：`work/base_units/draft/v7_units_draft.pilot_money_laundering_and_financial_crime.combined_audit.json`
   - 结果：59 个 direct unit、3 个 review item、6 个 parent/context item、审计 0 issue。
   - 规则：完整断言型 list item 可以作为 direct；只有标签的 bullet（如 `Structuring, microstructuring, smurfing:`）只进 `parent_items`，不作为 direct evidence。
   - 修正：`Financial institutions should:` 下的子项继承父项语义，归为 `obligation`，避免误归为 `risk_indicator`。
10. Glossary 路由过滤：已在 `build_fullbook_routing_dry_run.py` 中加入 glossary 状态机。
   - 遇到 `Glossary` heading 后，同章后续 glossary/acronym 词条统一标为 `ignored_glossary`。
   - 结果：750 个 glossary/acronym 块被过滤；后续 reviewed repairs 后，LLM grouping 请求为 1728。
   - `Governance process` 请求从 397 降到 13，说明该章原先的大量请求其实来自 glossary 词条。
11. 第二轮顺序 pilot：已按 batch plan 第一章 `Governance process` 从 offset 0 开始跑。
   - 切片：`work/base_units/llm_batches/governance_process.offset000_limit020.jsonl`
   - 切片 manifest：`work/base_units/llm_batches/governance_process.offset000_limit020.manifest.json`
   - 子代理原始决策：`work/base_units/llm_batches/pilot_governance_process_offset000_limit020_decisions.subagent.jsonl`
   - glossary 过滤后 replay 决策：`work/base_units/llm_batches/pilot_governance_process_offset000_limit020_decisions.filtered.jsonl`
   - 跨块残句 repair 后 replay 决策：`work/base_units/llm_batches/pilot_governance_process_offset000_limit020_decisions.repaired.jsonl`
   - LLM 物化：`work/base_units/draft/v7_units_draft.pilot_governance_process_offset000_limit020.llm.json`
   - combined 产物：`work/base_units/draft/v7_units_draft.pilot_governance_process_offset000_limit020.combined.json`
   - 修复：`v7en_b003677_s002` 与 `v7en_b003678_s001` 经 reviewed repair 合并为 `v7en_join_b003677_s002_b003678_s001`。
   - 结果：13 个请求、26 个 direct unit、0 个 review item、审计 0 issue。
   - 典型 direct：data governance 定义、data governance committee 职责、regulatory compliance obligation、committee oversight process、role-based access control。
   - 典型修复单元：`These outputs include suspicious activity reports, transaction monitoring outputs, data quality reports, and outcomes from oversight processes.`，页码 span 为 P489-P490。
12. `Data as an input for solutions` 顺序 pilot：已完成 offset 0-20、20-40、40-60、60-80、80-100、100-end 六个切片。
   - offset 0-20：combined direct 50、review 0、audit 0。
   - offset 20-40：combined direct 55、review 0、audit 0。
   - offset 40-60：默认 3 句宽度门下 combined direct 55、review 1、audit 0；4 句宽度门实验下 combined direct 56、review 0、audit 0。
   - offset 60-80：combined direct 47、review 0、audit 0。
   - offset 80-100：combined direct 43、review 0、audit 0。
   - offset 100-end：combined direct 50、review 0、audit 0。
   - 默认 3 句宽度门合计：combined direct 300、review 1、parent/context 7、audit 0。
   - 如果采用 offset 40-60 的 4 句宽度门实验结果，合计可变为 combined direct 301、review 0；但 4 句门仍未正式提升为默认规则。
   - 新增修复：保护 `<name>`、`<address>`、`<date of birth>` 这类教材字段，避免被 markdown/html 清洗误删。
   - 新增修复：短图示/OCR 文本如 `Voter registers`、`PEP databases`、`KYC information...` 进入 `ignored_visual_text_fragment`，不进入 LLM 分组。
   - 新增修复：`v7en_b003532_s003` + `v7en_b003533_s001` 合并为 `<date of birth>` 完整字段句。
   - 新增修复：`v7en_b003558_s004` + `v7en_b003559_s001` 合并为 `Because organizations need...` 完整跨页句。
   - 新增修复：`v7en_b003600_s002` + `v7en_b003601_s001` 合并为 `Data storage, however...` 完整跨块句。
   - 新增修复：`v7en_b003637_s003` + `v7en_b003638_s001` 合并为 `As new data becomes available...` 完整跨页句。
   - 结论：散文切分仍是“规则定位 + LLM/子代理语义分组 + 脚本回填原文”的混合流程，不是纯规则切分；LLM 只决定 `sentence_ids` 分组，不直接生成 `en_quote`。
   - 质量观察：弯引号/轻微编码痕迹不应直接导致 `needs_review`；只有残句、乱码或语义不可判定才进入 `needs_review`。
   - 质量观察：3 句 direct 单元总体可用，但“运营收益类三句概括”可能偏宽，后续 prompt 可继续压缩。
   - 宽度门：`--max-direct-sentences 4` 已加入物化脚本用于实验，但默认仍为 3，待更多切片验证后再决定是否正式放宽。
13. `Technology for KYC` 顺序 pilot：已跑 offset 0-20。
   - 结果：20 个请求、LLM direct 41、combined direct 41、review 0、parent/context 0、audit 0。
   - 新增修复：`v7en_b003129_s002` + `v7en_b003130_s001` 合并为 `The updated FATF recommendations...` 完整跨块句。
   - 新增修复：`v7en_b003135_s003` + `v7en_b003136_s001` 合并为 `This integration of government information...` 完整跨页句。
   - 新增修复：`v7en_b003149_s004` + `v7en_b003150_s001` 合并为 `It is a data-led practice... continuously updated.` 完整跨页句。
   - 典型 direct：FATF 对非面对面业务风险的口径、国家身份数据库的效率收益、国家身份数据库 honeypot 风险、perpetual KYC 触发项、perpetual KYC 不替代客户档案审查。
   - 质量观察：该批次说明流程能泛化到第二个章节；一个 3 句 perpetual KYC trigger unit 稍宽但仍在当前默认宽度门内。

下一步建议：

1. 继续抽审 `Data as an input for solutions` 六个 combined pilot，确认分组质量：
   - LLM 是否过度合并。
   - LLM 是否过度切分。
   - 教学导论、案例流水账、跨页残句是否被正确挡在 review。
   - `red_flag`、`case_fact`、`process` 的类型边界是否符合教研使用习惯。
   - 规则直出 list item 是否有过宽或误分类。
   - `parent_items` 是否确实只承担结构上下文，不被当成直接证据。
2. 固化章节级 decision manifest 格式：
   - 保存 request、model/prompt 信息、raw_response、parsed_response、input_hash、prompt_hash。
   - 物化默认 replay manifest，不重新调用 LLM。
   - 检查每个 request 的 sentence 覆盖率，漏句必须进 audit。
3. 按顺序继续时，可继续 `Technology for KYC` 的后续 offset，优先观察是否继续出现跨页残句和 3 句偏宽单元。
4. 第二轮抽审通过后，再补正式 `knowledge_zh` 生成策略。
5. 质量稳定后，再生成 `v7u_N*` 冻结 ID 和适配 `v7_units_as_cards.json`。

当前全书 dry-run 规模参考：

```text
total blocks: 4430
ignored/context blocks: 1369
rule-direct candidates: 1318
prose paragraphs needing LLM: 1726
estimated LLM windows: 1728
tables needing parser: 17
parseable table cells: 136
needs-review route: 0
ignored glossary/acronym blocks: 750
ignored visual/OCR text fragments: 35
```

已生成但尚未调用模型的全书 LLM 输入：

```text
work/base_units/llm_inputs/
├── v7_fullbook_llm_grouping_input.json
├── v7_fullbook_llm_grouping_input.jsonl
├── v7_fullbook_llm_grouping_manifest.draft.json
└── v7_fullbook_llm_grouping_input_report.md
```

该输入只用于下一步批量决策准备。正式调用前还需要确认：

- 是否按章节分批执行。
- 模型、温度、重试策略和 malformed JSON 处理。
- decision manifest 是否作为正式回放来源。
- 是否先跑 1-2 个章节进行人工抽审。

已生成章节批次计划草案：

```text
work/base_units/llm_batches/
├── v7_fullbook_llm_batch_plan.json
├── v7_fullbook_llm_batch_plan_report.md
└── <chapter-slug>.jsonl
```

批次计划只做两件事：

- 按章节拆分 1728 条 LLM 请求，方便分批跑。
- 标出 pilot 章节，优先抽审“长散文章 / 核心概念章 / 列表表格混合章”。

> 实验流水账（逐日跑批记录、overlay 叠加过程、修复示例）已剥离到同目录 实验日志_归档.md。

## 最终现况

本环节已于 2026-07-03 完成第一版正式冻结，不再是进行中的草稿。一页纸链路图见同目录 `UNIT_BUILD_PIPELINE.md`。

冻结结果：

| 指标 | 数量 |
|---|---:|
| formal units（正式知识单元） | 4973 |
| direct leaf units（可直接作证据） | 4702 |
| parent/context units（结构父/上下文） | 271 |
| excluded/review items（未冻结） | 10 |
| 重复 unit_id | 0 |
| 重复 direct sentence_id | 0 |
| 缺失 knowledge_zh | 0 |

正式产物位置：

```text
work/base_units/units/
├── v7_bilingual_units.json          ← 正式资产（4973 个冻结 unit）
├── v7_units_as_cards.json           ← adapter（v6 风格精简字段，供下游复用）
├── unit_freeze_manifest.json        ← tmp→formal 全量映射
├── excluded_or_review_manifest.json ← 10 个未冻结的 review
└── unit_build_report.md
```

构建链路概要（详见 `UNIT_BUILD_PIPELINE.md`）：

1. MinerU 中英分离 md → `prepare_base_blocks.py` 规则拆 block/英文拆句
2. 散文段落切 117 个章节切片 → 1724 个 DeepSeek 请求做英文句子分组
3. 脚本回填 `en_quote`、编号、去重 → 基底（direct=4399, review=234, parent=210）
4. 5 层 overlay 逐个修正具体问题 → 最终冻结输入（direct=4702, review=10, parent=271）
5. `freeze_formal_units.py` 排序、校验、重编号 → `v7_bilingual_units.json`

关键原则已守住：LLM 只决定"哪几句属于一个知识点"，`en_quote` 是脚本按 `sentence_ids` 从原文回填的，LLM 不写证据原文。每层 overlay 的痕迹留在 unit 的 `risk_flags` 字段里，可追溯。

下一步不属于本环节：

- 题目-选项-知识单元证据绑定（Phase 4，尚未开始）
- 教材知识图谱全书扩展（当前仅有前 5 章 pilot）
- 考点生成（尚未开始）

本环节到此为止，下游环节应读取 `v7_bilingual_units.json` 作为正式输入。
