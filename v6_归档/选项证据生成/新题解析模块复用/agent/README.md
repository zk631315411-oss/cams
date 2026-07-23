# Agentic Retrieval 工作区

本目录用于给“新题解析模块复用”补充一个受控的 agentic retrieval 层。

它不是通用聊天 Agent，也不是让 LLM 直接凭记忆决定答案。它的职责是：先让模型在不看教材的情况下暴露解题假设和选项判断逻辑，再把这些判断逻辑转成可执行的多路检索任务，最后用教材句卡验证、修正或推翻这些假设。

最终证据仍必须回到 `cards_v6_sentence.json` 中的真实教材句卡。

## 为什么需要 Agent 模式

当前主流程是整题直接检索：

```text
题干 + 全部选项
  -> BGE / BM25 / RRF
  -> exact / adjacent / KG
  -> rerank / MMR / parent block
  -> blind adjudicator
```

这个流程能覆盖常规题，但在以下场景容易漏证据：

- 多选题有多个知识方向，单一整题 query 可能只命中其中一个方向。
- 题目表述和教材术语不一致，例如题目是场景描述，教材是上位概念。
- 错误选项也需要反证，单纯整题检索更容易偏向正确项相关内容。
- 选项中某些关键词很弱，但恰好是判断答案的关键。

因此需要在检索前加入一层“解题假设 -> 检索任务”的转换。

## 核心原则

1. **盲态**：agent 的所有 LLM 阶段不能看到标准答案、教研解析、历史答案。
2. **先解题假设，后检索规划**：不要让 LLM 一上来凭空规划检索，而是先暴露它对题目的初步判断。
3. **检索任务可审计**：每条 query 都要能追溯到题目、选项或初判中的某个待验证命题。
4. **证据回归原文**：LLM 可以提出搜索方向，但最终引用只能是教材句卡。
5. **有限轮补搜**：最多 1-2 轮，防止成本和时间失控。
6. **最终裁判独立**：最终答案仍由 blind adjudicator/reviewer 判断，agent 只提供候选证据池和缺口说明。

## 目标流程

```text
输入题目
  |
  v
Stage 0: Blind Initial Reasoning
  - 只看题干和选项
  - 输出初判答案、每个选项的判断逻辑、待验证命题、可能教材主题
  |
  v
Stage 1: Search Task Builder
  - 输入题目 + Stage 0 初判
  - 将判断逻辑转成检索任务
  - 输出关键词检索、语义检索、选项级检索、反证检索 query
  |
  v
Stage 2: Hybrid Retrieval
  - 程序执行 BGE / BM25 / RRF / exact / adjacent / KG
  - 合并去重、rerank、MMR、父块替换
  |
  v
Stage 3: Evidence Gap Audit
  - 输入题目 + 初判 + 当前候选证据
  - 判断每个选项是否已有 direct evidence
  - 输出缺口和补搜 query
  |
  v
Stage 4: Limited Follow-up Retrieval
  - 仅对缺口执行 1-2 轮补搜
  - 新证据继续合并进候选池
  |
  v
Stage 5: Final Blind Adjudicator
  - 只基于最终候选教材句卡判断答案
  - 输出选项解析和 evidence_cards
```

## Stage 0: Blind Initial Reasoning

### 输入

```json
{
  "stem": "题干",
  "options": {
    "A": "选项 A",
    "B": "选项 B"
  },
  "question_type": "single_choice/multiple_choice/unknown"
}
```

### 输出

```json
{
  "initial_answer": ["A"],
  "confidence": "high/medium/low",
  "question_focus": "这道题表面上在考什么",
  "option_hypotheses": [
    {
      "option": "A",
      "claim": "选项表达的可验证命题",
      "initial_judgement": "likely_correct/likely_incorrect/uncertain",
      "reasoning": "为什么初步这样判断",
      "needs_evidence_for": [
        "需要教材验证的关键点"
      ]
    }
  ],
  "possible_textbook_topics": [
    "可能涉及的教材主题或术语"
  ]
}
```

### 要点

- 这一阶段允许模型凭通用能力初判，但必须显式标注“不确定”和“待验证命题”。
- 不要求它给最终答案。
- 不允许引用不存在的教材依据。

## Stage 1: Search Task Builder

### 输入

题目 + Stage 0 输出。

### 输出

```json
{
  "search_tasks": [
    {
      "task_id": "t1",
      "target": "whole_question/option_A/option_B/contrast",
      "source_hypothesis": "来自 Stage 0 的哪个判断点",
      "search_mode": "semantic/keyword/exact/contrast",
      "queries": [
        "短查询 1",
        "短查询 2"
      ],
      "must_terms": [
        "关键术语"
      ],
      "why": "为什么需要搜这组 query"
    }
  ]
}
```

### 检索任务类型

- `whole_question`：整题考查方向。
- `option_X`：某个选项的直接支持或反驳。
- `contrast`：用于区分两个相似选项或阶段。
- `definition`：定义、分类、制度要求。
- `red_flag`：危险信号、典型特征。
- `process_stage`：洗钱阶段、流程、场景判断。

## Stage 2: Hybrid Retrieval

程序层执行，不让 LLM 直接挑最终证据。

每个 search task 分别执行：

```text
query
  -> BGE
  -> BM25
  -> RRF
  -> exact phrase append
  -> adjacent card append
  -> KG append
  -> rerank
  -> MMR
  -> parent block / short context expansion
```

输出候选证据时必须保留：

- `card_id`
- `citation`
- `expanded_text` 或 `passage`
- `source_task_id`
- `retrieval_sources`
- `score`
- `rank`

## Stage 3: Evidence Gap Audit

### 输入

题目、Stage 0 初判、候选证据池。

### 输出

```json
{
  "coverage_by_option": [
    {
      "option": "A",
      "coverage": "direct/partial/none/conflict",
      "supporting_card_ids": ["v6s_N00001"],
      "missing_points": ["还缺什么教材证据"],
      "needs_followup": true
    }
  ],
  "followup_tasks": [
    {
      "target": "option_A",
      "queries": ["补搜 query"],
      "why": "为什么需要补搜"
    }
  ],
  "stop_reason": "sufficient/needs_followup/max_rounds/manual_review"
}
```

### 要点

- 它不是最终裁判，只判断“证据池是否覆盖判断需求”。
- 如果某个选项缺 direct evidence，要明确缺口。
- 补搜 query 必须来自缺口，不允许无边界扩散。

## Stage 4: Limited Follow-up Retrieval

默认最多 1 轮，必要时可配置为 2 轮。

停止条件：

- 每个选项都有 direct/partial evidence，且无明显冲突。
- 没有新的 followup task。
- 达到最大轮数。
- 候选池超过上限。

## Stage 5: Final Blind Adjudicator

最终裁判只接收：

- 题干
- 选项
- 最终候选教材句卡

它不能看到：

- 标准答案
- 教研解析
- Stage 0 的初判答案作为“答案提示”

可以看到 Stage 0/3 的内容吗，需要谨慎处理：

- 可以看“待验证命题”和“证据缺口摘要”。
- 不建议看 `initial_answer`，避免锚定。
- 若保留初判信息，必须删除初判答案，只保留选项级 claim。

## 与 WeKnora / ima 的关系

WeKnora 的 Agent 是通用 ReAct：

```text
LLM 决定工具
  -> grep_chunks / knowledge_search / list_knowledge_chunks / graph
  -> 观察结果
  -> 决定是否继续
```

本模块不完整照搬通用 ReAct，而是提取其中对题目证据绑定最有价值的部分：

- 多轮检索
- 关键词与语义检索切换
- 深读后判断缺口
- 根据缺口补搜

区别是：本模块更受控，所有阶段都落 JSON，且最终证据必须绑定教材句卡。

## 计划文件结构

```text
agent/
  README.md                 # 本文件，定义流程与边界
  ACCEPTANCE.md             # 验收标准
  prompts/
    stage0_initial_reasoning.md
    stage1_search_task_builder.md
    stage3_evidence_gap_audit.md
  schemas/
    initial_reasoning.schema.json
    search_tasks.schema.json
    evidence_gap_audit.schema.json
  experiments/
    README.md
  outputs/
    .gitkeep
```

## 第一阶段实现目标

第一阶段不直接替换主流程，只做旁路验证：

1. 输入一题。
2. 跑 Stage 0 初判。
3. 跑 Stage 1 检索任务生成。
4. 复用现有检索函数执行多路检索。
5. 跑 Stage 3 证据缺口审查。
6. 输出完整 debug JSON。
7. 和当前直接整题检索做横向对比。

只有当旁路验证证明能补到直接检索漏掉的关键证据，再接入 `run_bindings.py`。
