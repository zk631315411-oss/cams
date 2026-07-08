# CAMS 教材证据驱动解析系统：Agentic Evidence Search 计划

## 0. 当前结论

本计划已经从“LightRAG 裸检索可行性验证”升级为：

```text
AI 主导的、受约束的、可审计的 agentic evidence search 系统
```

LightRAG 的定位也随之调整：

```text
LightRAG = 底层候选检索工具之一
AI Controller = 主导搜索、读证据、判断缺口、生成证据链的核心模块
```

项目最终目标不是“根据旧解析找证据”，而是：

```text
题目 + 选项 + 正确答案 + 教材
→ 系统自己检索教材证据
→ 判断证据如何支持/反证选项
→ 写出可追溯解析
→ 解析经证据审计与教研审核
→ 用已审计解析 + 教材证据 + 学生问题做答疑
```

生产链路中禁止使用旧解析、教研答疑、手工证据包作为检索输入。它们只能用于检索完成后的评估、审计和回归测试。

---

## 1. 为什么要升级为 Agentic Search

### 1.1 A0 已完成结果

DeepSeek 按原计划执行 A0 “完整题目裸查”后，结果为：

```text
Recall@15 = 1/4
Noise@15 = 15（按原记录口径）
命中：E1 v6_b03_N18
漏召回：E2 / E3 / E4
```

现象：

- 完整题目包含 A/E 正确选项和 D 干扰项。
- LightRAG 抽取出的焦点偏向“盈利业务减少或损失”“调查费用和罚金增加”“洗钱对金融机构的后果”。
- “公司税”的信号被稀释。
- E1 能召回，说明 LightRAG 能识别“这题考 FI 影响”。
- E2/E3/E4 全漏，说明完整题目单次检索无法跨到 D 选项所需的反证证据。

补充审计项：

- `Noise@15=15` 与“命中 E1”在常规定义下可能不一致，后续需要统一噪声统计函数。
- 原始 A0 结果仍作为失败基线保留，不再把 A0 作为生产接入门槛。

### 1.2 文献支持给出的启示

`文献支持` 中三篇 agentic search / agentic RAG 文献共同支持以下判断：

- 单次 RAG 会把候选证据集过早固定，复杂题目容易漏掉关键证据。
- Agentic search 的核心是让模型多步决定“查什么、读什么、缺什么、是否继续”。
- 有效系统应使用有限步、带预算、带停止条件、可审计的检索控制，而不是无限递归子问题。
- 高相似 chunk 不等于高证据效用，证据必须能帮助最终选项归因和解析正确。
- 后续查询应能吸收前一步召回内容中的术语，但要留下轨迹，便于审计。

对应到 CAMS：

```text
完整题目裸查失败
→ 不是继续调裸 query
→ 而是进入选项级 / 命题级 / 缺口驱动的 agentic evidence search
```

---

## 2. 输入边界

### 2.1 生产解析阶段允许输入

- 题干
- 全部选项
- 正确答案
- 教材原文
- 教材卡片
- 教材索引
- 系统本轮已召回的教材候选

### 2.2 生产解析阶段禁止输入

- 现有解析
- 教研答疑
- 学生答疑历史
- 手工证据包
- `claim_evidence_frames.json` 中已写好的证据方向
- 之前 AI 对同题做过的分析结果

### 2.3 学生答疑阶段允许额外输入

学生答疑阶段必须发生在解析通过审计之后，允许额外输入：

- 学生具体问题
- 已生成且经过证据审计/教研审核的解析
- 已确认的证据归因表
- 已确认的教材证据引用

### 2.4 评估材料用途

以下材料只能用于事后评估，不能进入生产检索提示词：

- 旧解析
- 教研答疑
- `claim_evidence_frames.json`
- 手工 evidence anchors
- 人工整理的证据包

验收：

```text
生产检索日志中出现上述禁止输入，判定该实验无效。
```

---

## 3. 系统目标

### 3.1 要实现的能力

AI Controller 需要完成：

1. 读取题目、选项、正确答案。
2. 先分析题干，判断这题考教材中的哪个主考点、列表、定义或流程。
3. 先检索主考点框架证据，而不是先逐个选项硬搜。
4. 将选项映射到主考点框架，判断哪些选项被框架直接支持、方向相反或不在框架内。
5. 将无法由主框架解释的选项改写为可判断的命题。
6. 为这些异常/干扰选项规划补充检索 query。
7. 调用 LightRAG / baseline 检索教材候选。
8. 阅读候选 chunk 和相邻教材卡片。
9. 判断当前证据是否支持、反证、解释误解或无关。
10. 识别证据缺口。
11. 基于已召回教材内容生成下一步查询。
12. 在预算内重复搜索、阅读、归因。
13. 建立 evidence ledger。
14. 生成可追溯解析。
15. 输出审计报告。

### 3.2 不要实现的东西

当前阶段不做：

- 不做完整学生聊天系统。
- 不做大规模微调。
- 不训练专用 retriever。
- 不让模型基于旧解析倒推证据。
- 不以最终回答流畅度作为检索通过标准。

当前阶段只验证：

```text
AI 主导搜索后，能否在不泄漏旧解析/人工证据的条件下找到教材证据链。
```

---

## 4. Ground Truth 与主测试题

### 4.1 测试题

- `question_id`: `2.1_19`
- 题型：多选题
- 题干：洗钱会对金融机构 FI 造成哪些后果？选择两个。
- 正确答案：`A, E`
- 目标干扰项：`D 公司税的增加`

### 4.2 四组核心证据

| 证据组 | 含义 | 必须命中 / 可替代卡片 |
|---|---|---|
| E1 | 税收损失：洗钱导致政府税收缩水 | 必须命中 `v6_b03_N18`，可接受相邻 `v6_b03_N17/v6_b03_N19` |
| E2 | 贸易洗钱避税：操纵贸易价格、避税 | 命中 `v6_b29_N05` 或等价机制卡，如 `v6_b33_N20/v6_b33_N25` |
| E3 | 空壳公司、虚假发票、VAT、税务欺诈 | 命中 `v6_b33_N23` 或 `v6_b33_N24/v6_b33_N25` |
| E4 | BMPE 规避国内税收和关税 | 必须命中 `v6_b33_N38` 或同段等价卡 |

这些证据组是评估 ground truth，不是生产检索输入。

### 4.3 D 选项正确归因

D 的命题是：

```text
洗钱会导致金融机构 FI 的公司税增加。
```

正确反证链应说明：

- 教材说的是政府税收缩水，而不是 FI 公司税增加。
- 贸易洗钱、虚假发票、BMPE 等机制通常指向逃税、避税、规避关税。
- 税收影响的主体多是政府、犯罪分子、贸易参与者或进口商，不是金融机构承担更高公司税。
- D 错在主体错配和方向错配。

验收：

```text
D 选项解析必须同时说出“主体错配”和“方向错配”。
```

---

## 5. 指标定义

### 5.1 召回指标

```text
EvidenceGroupRecall@K = 命中的证据组数 / 目标证据组数
BestRank(Ei) = 证据组 Ei 首次出现的候选排名
SelectedEvidenceRecall = 最终 evidence ledger 中命中的证据组数 / 目标证据组数
```

### 5.2 噪声指标

候选 chunk 满足以下任一条件，不算噪声：

- 属于 E1-E4 任一证据组。
- 能直接支持 A/E 正确答案。
- 能直接反证 D。
- 能解释学生常见误解，但必须可回链教材。

其他 chunk 记为噪声。

```text
Noise@K = Top-K 中噪声 chunk 数
Precision@K = 1 - Noise@K / K
FinalEvidencePrecision = 最终 evidence ledger 中有效证据数 / ledger 总证据数
```

### 5.3 可追溯指标

```text
Traceability = 可反查 card_id/source_id 的候选数 / 候选总数
CitationCoverage = 解析中有教材引用的关键判断数 / 解析中关键判断总数
```

要求：

```text
Traceability = 100%
CitationCoverage = 100%
```

### 5.4 Agentic Search 控制指标

```text
MaxSearchStepsPerQuestion <= 10
MaxSearchStepsPerOption <= 4
MaxQueriesPerSearchCall <= 5
NoLeakage = 100%
DuplicateLoopCount <= 1
```

重复循环定义：

```text
连续两次 query 高度相似，且召回结果重叠高，且没有引入新的有效证据。
```

处理规则：

```text
出现重复循环后，下一步必须执行 broaden / facet pivot / stop，不允许继续近义重复检索。
```

---

## 6. Agentic Evidence Search 流程

### 6.1 总流程

```text
题目 + 选项 + 正确答案
→ 题干级考点框架识别
→ 主考点框架检索
→ 打开主框架教材卡片和相邻卡片
→ 选项映射到主框架
→ 标记框架内支持 / 方向相反 / 框架未覆盖
→ 对框架未覆盖或存在误解的选项做命题拆解
→ 为异常/干扰选项生成补充检索意图
→ LightRAG / baseline 检索补充证据
→ 读取候选 chunk
→ 打开相邻 card / source window
→ 建立 evidence ledger
→ 判断缺口
→ 生成后续 query
→ 重复直到证据充分或预算耗尽
→ 生成选项归因
→ 生成可追溯解析
→ 输出审计报告
```

### 6.1.1 人类做题式约束

AI Controller 必须先回答：

```text
这道题题干在问教材中的哪个主考点？
教材是否存在总表、定义、流程或框架可以直接覆盖多数选项？
```

只有当主考点框架检索失败，或某个选项无法由主框架解释时，才进入选项级补充检索。

以 `2.1_19` 为例，合理路径是：

```text
题干：洗钱会对金融机构 FI 造成哪些后果？
→ 判断为“洗钱对金融机构的负面影响/后果列表”题
→ 先检索金融机构后果总表
→ 目标应命中 `v6_b04_N09` 或等价框架卡
→ 用总表映射 A/B/C/E
→ D 涉及税收误解，单独补查税收主体和方向
```

禁止把系统主流程写成：

```text
A 单独搜一次
B 单独搜一次
C 单独搜一次
D 单独搜一次
E 单独搜一次
```

逐选项检索只能作为补充策略，不能替代题干级主框架检索。

### 6.2 每一步必须记录

每次搜索都要写入 trajectory log：

```json
{
  "step_id": 1,
  "level": "question_frame | option_mapping | option_claim",
  "option": "D",
  "claim": "洗钱会导致金融机构FI的公司税增加",
  "target_frame": "洗钱对金融机构的负面影响/后果列表",
  "intent": "先定位主考点框架，再判断 D 是否需要补充反证",
  "query": "...",
  "strategy": "specialization | generalization | exploration | verification",
  "allowed_inputs": ["question", "options", "answer", "retrieved_text"],
  "retriever": "lightrag_mix",
  "top_k": 15,
  "new_evidence": ["v6_b03_N18"],
  "gap_after_step": ["贸易洗钱避税机制", "虚假发票税务欺诈", "BMPE关税规避"],
  "decision": "continue"
}
```

### 6.3 Evidence Ledger 格式

```json
{
  "evidence_id": "E1",
  "card_id": "v6_b03_N18",
  "source_text": "...",
  "role": "contradict_option | support_correct_option | explain_misconception | background",
  "frame_role": "main_frame | option_specific | exception_evidence",
  "target_option": "D",
  "claim_relation": "subject_mismatch | direction_mismatch | direct_support | irrelevant",
  "confidence": 0.0,
  "used_in_explanation": true
}
```

验收：

- 每条最终证据必须有 `card_id`。
- 每条最终证据必须有 `role`。
- 每条最终证据必须标注 `frame_role`。
- 每条最终证据必须绑定到选项或全题考点。
- 不能只有“相关”，必须说明“支持/反证/解释误解/背景”。

---

## 7. 检索工具接口

### 7.1 必需工具

| 工具 | 作用 | 可由什么实现 |
|---|---|---|
| `search_cards(query, mode, top_k)` | 全局召回候选教材卡片 | LightRAG / BM25+BGE+RRF |
| `open_card(card_id)` | 打开指定卡片完整内容 | 本地 cards 索引 |
| `open_neighbors(card_id, window)` | 打开相邻教材卡片 | 本地 cards 索引 |
| `find_in_cards(patterns, scope)` | 在候选卡片或章节内做精确查找 | 本地关键词 |
| `merge_rerank(candidates)` | 多 query 合并、去重、重排 | RRF / reranker |
| `write_ledger(evidence)` | 写入证据账本 | 本地 JSON |

### 7.2 LightRAG 接入要求

LightRAG 只在满足以下条件时可进入主线：

- 能返回 raw chunks / references。
- 每个 chunk 能反查 `card_id` 或稳定 `source_id`。
- 支持 `mix` 或等价模式。
- 支持 query data，不只返回最终回答。

不满足时：

```text
LightRAG 不进入主线，继续使用现有 baseline 检索器做工具底座。
```

---

## 8. 原子实验计划

### P0：输入边界与泄漏检查

目的：确保生产实验没有用旧解析或人工证据包。

验收：

- 检索 prompt 中不出现旧解析、教研答疑、手工 anchors。
- 检索 prompt 中不出现 `claim_evidence_frames.json` 的 evidence anchors。
- 每次实验输出 `leakage_check.json`。
- `NoLeakage = 100%`。

### P1：语料与可追溯性检查

输入：

- `cams工作台/data/cards_ch2.json`

产物：

- `data/lightrag_eval/cards_lightrag_docs.jsonl`
- `data/lightrag_eval/card_doc_stats.json`

验收：

- 每条文档显式包含 `CARD_ID`。
- E1-E4 目标卡片均存在。
- 空文本、重复 card_id 为 0。
- 通过 LightRAG 返回的 chunk 能反查 card_id。
- `Traceability = 100%`。

### P2：A0 失败基线固化

目的：把已完成 A0 作为裸查失败基线记录下来。

产物：

- `data/lightrag_eval/test_A0_analysis_blind/metrics.json`
- `data/lightrag_eval/test_A0_analysis_blind/diagnostic.md`

验收：

- 记录 `Recall@15 = 1/4`。
- 记录 E1 命中、E2/E3/E4 漏召回。
- 记录 query 被 A/E 正确项吸走焦点的诊断。
- 统一复核 `Noise@15` 口径。

### P3：选项命题拆解

目的：让系统从题目和选项中生成待验证命题，不引入证据 anchor。

输入：

```text
题干 + A/B/C/D/E + 正确答案 A,E
```

输出示例：

```json
[
  {
    "option": "D",
    "claim": "洗钱会导致金融机构FI的公司税增加",
    "expected_relation": "likely_false",
    "needed_checks": ["金融机构后果", "税收影响主体", "税收方向"]
  }
]
```

验收：

- 每个选项都有 claim。
- D claim 不包含 oracle 词：政府税收缩水、贸易洗钱、虚假发票、BMPE。
- D 的 `needed_checks` 至少包含主体和方向。

### P4：Agentic Search 单选项验证 D

目的：验证 AI Controller 能否围绕 D 选项主动补齐反证链。

生产合法输入：

- 题干
- 选项
- 正确答案
- 教材检索工具返回的候选

禁止输入：

- 旧解析
- 教研答疑
- 手工 E1-E4 anchor

建议首轮 query：

```text
题目问洗钱对金融机构FI造成哪些后果。D选项声称洗钱会导致金融机构FI的公司税增加。请检索教材中能判断该选项对错的内容，重点关注税收影响的主体和方向。
```

后续 query 必须由 AI 基于已召回教材内容和缺口生成。

验收：

```text
AggregatedEvidenceRecall@30 >= 3/4
SelectedEvidenceRecall >= 3/4
必须命中 E1
FinalEvidencePrecision >= 0.70
Traceability = 100%
SearchStepsForD <= 4
D 归因必须包含主体错配 + 方向错配
```

升级验收：

```text
SelectedEvidenceRecall = 4/4
SearchStepsForD <= 4
FinalEvidencePrecision >= 0.80
```

失败处理：

- 若只命中 E1，说明仍停留在裸查水平，需增加 facet pivot。
- 若召回税务证据但无法反证 D，说明 Evidence Attribution 模块失败。
- 若命中 E2/E3/E4 但用了 oracle 词，实验无效。

### P5：Agentic Search 全选项验证

目的：验证系统能同时支持 A/E 正确项，并反证 B/C/D。

验收：

- A/E 至少各有 1 条直接或等价教材证据。
- B/C/D 至少各有一个明确归因：反证、无教材支持、主体错配、方向错配或概念错配。
- D 达到 P4 验收。
- 全题 `SearchSteps <= 10`。
- Evidence ledger 中无无法追溯证据。

### P6：解析生成

输入：

- 题目
- 正确答案
- evidence ledger
- 选项归因表

禁止：

- 禁止输入旧解析。

验收：

- 解析能说明 A/E 为什么正确。
- 解析能说明 D 为什么错误。
- D 错误原因包含主体错配和方向错配。
- 每个关键判断都有 citation。
- 不出现教材证据无法支持的扩写。
- 解析中所有引用能回链 card_id。

### P7：审计报告

输出：

- `final_decision_report.md`

必须包含：

- 检索轨迹。
- 每一步 query 和策略。
- 每一步新增证据。
- Evidence ledger。
- E1-E4 命中矩阵。
- 噪声样例。
- 泄漏检查结果。
- D 选项归因检查。
- 是否进入多题验证的结论。

---

## 9. Oracle 上限测试

Oracle 测试只用于诊断 LightRAG 上限，不作为生产门槛。

输入：

- `claim_evidence_frames.json` 中的人工 anchors。

验收：

```text
OracleRecall@15 = 4/4
Traceability = 100%
```

解释：

- Oracle 通过但 P4/P5 失败：问题在“题目语言到教材证据语言”的自动跨越。
- Oracle 失败：LightRAG 作为检索工具本身也不适合该任务。

---

## 10. 决策规则

| 结果 | 决策 |
|---|---|
| P4 通过，P5 通过 | 进入多题验证 |
| P4 通过，P5 失败 | 先做选项级 controller，不做全题一次性 controller |
| P4 失败，Oracle 通过 | 检索器有上限，controller 的 query planning / gap detection 不足 |
| P4 失败，Oracle 失败 | LightRAG 不接入主线 |
| Traceability 不达标 | 无论召回多好，都不接入主线 |
| NoLeakage 不达标 | 实验无效，必须重跑 |

进入多题验证的最低条件：

```text
P0 通过
P1 通过
P4 通过
P6 通过
Traceability = 100%
NoLeakage = 100%
```

---

## 11. 多题扩展

`2.1_19 D` 通过后，增加 3-5 道题：

- `2.1_4`：处置阶段，教材直给型。
- `2.2_6`：PEP 风险重分类，流程/对象辨析型。
- `2.2_9`：巢状交易，概念定义 + 风险解释型。
- 另选 1 道教材证据弱、推理为主的题。

多题验收：

```text
每题 SelectedEvidenceRecall >= 3/4 或达到该题 ground truth 要求
平均 FinalEvidencePrecision >= 0.75
Traceability = 100%
NoLeakage = 100%
每题 SearchSteps <= 10
至少覆盖直给型、跨节证据链型、概念/流程辨析型
```

---

## 12. 代码与产物

### 12.1 新增代码

| 文件 | 作用 | 验收 |
|---|---|---|
| `agentic_search_controller.py` | AI 搜索控制器 | 能执行有限步 search/read/gap/continue/stop |
| `claim_decomposer.py` | 选项命题拆解 | 输出每个选项 claim 与 needed_checks |
| `retrieval_tools.py` | 检索工具封装 | 支持 LightRAG 和 baseline |
| `card_reader.py` | 打开 card 与相邻 card | 能按 card_id 取原文 |
| `evidence_ledger.py` | 证据账本 | 每条证据可追溯、可归因 |
| `agentic_eval.py` | 评估指标 | 输出 recall/noise/traceability/leakage |
| `explanation_generator.py` | 基于 ledger 写解析 | 不读旧解析 |

### 12.2 输出目录

```text
cams工作台/data/agentic_search_eval/
  00_input_boundary_check/
  01_traceability_check/
  02_A0_frozen_baseline/
  03_claim_decomposition/
  04_agentic_D_search/
  05_agentic_all_options/
  06_explanation_generation/
  07_final_audit/
  final_decision_report.md
```

### 12.3 最终交付

必须交付：

- `final_decision_report.md`
- `trajectory_log.jsonl`
- `evidence_ledger.json`
- `hit_matrix.json`
- `metrics.json`
- `leakage_check.json`
- `generated_explanation.md`

---

## 13. 时间盒

| 阶段 | 时间盒 | 超时处理 |
|---|---:|---|
| P0 输入边界检查 | 20 分钟 | 不通过则停止 |
| P1 可追溯检查 | 40 分钟 | card_id 不稳定则先修语料 |
| P2 A0 结果固化 | 20 分钟 | 只记录，不重跑也可 |
| P3 命题拆解 | 40 分钟 | 先只做 `2.1_19` |
| P4 D 单选项 agentic search | 90 分钟 | 超时输出失败轨迹 |
| P5 全选项 agentic search | 120 分钟 | 可延后，P4 先通过 |
| P6 解析生成 | 60 分钟 | 证据不足则不生成完整解析 |
| P7 审计报告 | 60 分钟 | 必须输出明确结论 |

---

## 14. 风险清单

| 风险 | 观察信号 | 应对 |
|---|---|---|
| 误把评估证据当输入 | query 中出现人工 anchor | P0 泄漏检查，实验判无效 |
| AI 继续裸查 | 多步 query 只是完整题目改写 | 强制 option claim + gap list |
| 重复循环 | 连续 query 高相似且无新证据 | 触发 broaden / exploration / stop |
| 只支持正确项，不反证干扰项 | A/E 证据多，D 缺反证 | 选项级搜索，不做全题一次 query |
| 命中税务证据但归因错 | 把避税解释成 FI 税负增加 | Evidence Attribution 必查主体和方向 |
| LightRAG 丢失 card_id | raw chunk 无法回链 | 不接入主线，先修 source_id |
| 证据噪声高 | ledger 中大量泛泛相关 chunk | FinalEvidencePrecision 设门槛 |
| 解析幻觉 | 解析出现 ledger 外判断 | CitationCoverage 100%，审计拦截 |
| 成本过高 | search steps 或 token 超预算 | intent-adaptive budgeting，先 D 后全题 |

---

## 15. 当前下一步

立即执行顺序：

1. 固化 A0 失败报告，复核噪声口径。
2. 实现或模拟 P3 选项命题拆解。
3. 实现 P4：D 选项 agentic search。
4. 输出 trajectory log 和 evidence ledger。
5. 用 E1-E4 做事后评估。
6. 若 P4 通过，再做 P5 全选项和 P6 解析生成。

当前项目判断：

```text
裸 LightRAG 不能直接解决问题。
LightRAG 仍可能作为检索工具有价值。
真正要实现的是 AI 主导的搜索控制器。
下一阶段的成败取决于 P4：D 选项 agentic evidence search 是否能在不泄漏人工证据的条件下召回并归因 E1-E4。
```
