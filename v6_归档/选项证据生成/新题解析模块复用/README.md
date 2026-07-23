# 新题解析模块复用

将 CAMS 教材 5199 张句卡与考试题目自动匹配，为每道题的每个选项
找到教材原文依据，输出"题目-选项-句卡"绑定结果。

## 系统定位

**辅助工具**——帮老师缩小搜索范围，从 5199 张句卡中快速定位每道题的
教材原文依据。AI 自动给出答案和证据卡片，标记不确定的题供人工复核。

## 当前基准（2026-06-29）

全书 2-5 章全量测试：

| 指标 | 数值 |
|---|---|
| 题目级一致率 | 565/702（80.5%） |
| 已跑题目 | 703 题（章 2-5） |
| AI ≠ 题库 | 137 题（标 needs_teacher_review） |
| 题库无答案 | 1 题 |
| 单题耗时 | ~40-70 秒（pro 裁判，视题目复杂度） |
| 20 并发全书耗时 | ~40 分钟 |

错题模式（抽样分析）：
- focus_misdirected：裁判被干扰证据吸走，选了有强卡片但题库不要求的选项
- retrieval_gap：正确答案所需句卡不在候选池中，裁判无卡可引
- conflict_multiple_correct：单选题多选项均有 direct 证据，无法自动判定
- evidence_inflation：裁判将间接相关标为 direct，引用可信度不足

### 各章一致率

| 章 | 题数 | 一致率 |
|---|---|---|
| 2.1-2.8 | 179 | 82% |
| 3.1-3.6 | 202 | 82% |
| 4.1-4.5 | 208 | 79% |
| 5.1-5.3 | 110 | 73% |

### 管线架构（精简后）

每道题 2 次 API 调用：Flash 精排（分批 ~8 次轻量调用）+ 盲判裁判（1 次 pro+high）。已砍掉复核员和 LLM 二审（与裁判输入相同，无增量价值）。

## 当前核心流程

检索管线：选项文本作查询 → BGE+BM25 取并集 → 术语映射扩展 exact_phrase
→ KG 导航召回 → 邻卡扩展 → Cross-Encoder 精排 → Composite 分 →
Jaccard MMR 去冗余 → 父块替换 → 短上下文扩展 → 裁判 LLM 批量判断。

```text
题目(题干+全部选项)
  -> 检索
       - 只使用选项文本作查询（去掉题干噪声）
       - BGE (card_bge) + BM25 并列检索
       - 取并集（Union），保留原始分，不做 RRF
       - 术语映射扩展 must_terms → exact_phrase 搜索
       - 可选 KG 导航召回 v6s 句卡挂载 (append + 去重)
       - 沿兄弟链表扩展邻卡（window=3）
  -> 精排 (Flash Rerank)
       - CE passage: knowledge + citation（短句，避开父块噪声）
       - 分批 40 条送 DeepSeek Flash 打分 0-10 → 归一化到 0-1
       - composite_score: 0.6×llm_rerank + 0.3×retrieval + 0.1×sourceWeight
       - 备选：本地 Cross-Encoder GPU（--no-llm-rerank）
  -> MMR 去冗余
       - Jaccard bigram MMR (λ=0.7, top_k×4)
  -> Merge
       - resolveParentChunks: H4 父块段落替换子块 expanded_text
       - expandShortContextWithNeighbors: <350 字沿链表扩展
       - candidates_for_adjudicator_prompt: 邻卡上下文 + KG 节点定义 → 裁判
  -> Blind Adjudicator
       - deepseek-v4-pro, reasoning_effort=high
       - 一次判断所有选项 correct/incorrect/insufficient/needs_manual
       - 看不到题库答案（盲判）
  -> 答案确定
       - 同卡冲突检测（判断题）
       - 单选题多 direct 退回人工
       - 多选题合并 direct + predicted
       - 全部 insufficient → 标 review
  -> AI ≠ 题库答案时 → 规则诊断分歧类型，标 needs_teacher_review
  -> JSON / JSONL 输出
```

### 与 WeKnora 的关键差异

| 环节 | WeKnora | 我们 | 原因 |
|---|---|---|---|
| 查询 | LLM Rewrite | 选项文本，不做改写 | 考题表达精准 |
| 融合 | RRF 0.7/0.3 | Union 取并集 | 单句卡 BGE 弱，RRF 惩罚 BM25 好结果 |
| 图谱 | Neo4j CONTAINS | BGE → KG nodes | 知识概念级节点 |
| Embedding | 标题面包屑+正文 | KNOWLEDGE+CITATION+SECTION | 句卡级卡片 |
| 裁判上下文 | 段落级 chunk | 单句+邻卡上下文+KG节点定义 | 句卡太短需补上下文 |

## 快速开始

```powershell
cd "D:\守正公司工作区\cams考试\cams工作台（重构版）\tools\选项证据生成\新题解析模块复用"

# 跑前 20 题（推荐并发 7）
python .\run_bindings.py --limit 20 --concurrency 7

# 跑指定题
python .\run_bindings.py --ids 2.1_19 2.1_22 --concurrency 7

# 强制重跑
python .\run_bindings.py --ids 2.1_19 --force

# 关闭 KG 召回（A/B 对照）
python .\run_bindings.py --ids 2.1_19 --no-kg-recall
```

## 输出

```text
output/
  questions/q_{question_id}.json     ← 每题完整 pipeline 过程
  question_option_card_bindings.jsonl ← 选项级绑定表
  summary.json                       ← 执行汇总
  cache/retrieval_*.pkl              ← BGE/BM25 缓存
```

绑定表字段要点：

```text
强证据 / 可直接入解析：evidence_card_ids、evidence_cards
弱关系 / 候选：candidate_card_ids
逐卡强弱标注：relation_strengths
需人工复核：needs_teacher_review、teacher_review_reason
```

## 项目结构

```
新题解析模块复用/
  run_bindings.py              ← 入口 + CLI + main()
  plan_b.py                    ← Plan B：答案知情证据定位（--plan-b）
  rerank_server.py             ← CE 精排服务（GPU 备选，端口 8000）
  formal_quality_report.py     ← 独立质量报告生成工具
  README.md

  retrieval/
    __init__.py
    cross_encoder.py           ← Flash 精排 + CE HTTP 客户端
    card_graph.py              ← 句卡链表、父块索引、短/邻卡扩展、父块替换
    passage_score_mmr.py       ← passage 构建、复合分、Jaccard MMR
    enrich.py                  ← 候选富集（nearby + KG 节点定义）
    rrf.py                     ← RRF 融合（仅 followup 轮次使用）
    terminology_map.py         ← 题目术语 → 教材术语 手工映射表
    blind_guard.py             ← 备用：盲判题目脱敏（从 run_bindings 拆分）
    repair_hint.py             ← 备用：盲判修复提示（从 run_bindings 拆分）

  stages/
    __init__.py
    llm.py                     ← LLM 客户端、阶段路由、模型配置

  agent/                       ← [历史实验] Agentic Retrieval
    README.md                  ← 完整设计文档（5 阶段流程）
    ACCEPTANCE.md              ← 验收标准
    prompts/                   ← Stage 0/1/3 的 LLM prompt
    schemas/                   ← 各阶段 JSON schema
    experiments/               ← 实验记录

  logs/                        ← 运行日志
  output/                      ← 管线产物
  项目冗余测试/
    pyproject.toml             ← vulture 死代码检测配置
    whitelist.py               ← vulture 误报白名单
    run_vulture.ps1            ← 死代码检测运行脚本
```

### agent/ 历史实验

在检索前加入"解题假设 → 检索任务"的转换层，解决整题检索在以下场景的不足：
多选题多知识方向、题目表述与教材术语不一致、错误选项需要反证。

流程设计为 5 阶段：Blind Initial Reasoning → Search Task Builder → Hybrid Retrieval → Evidence Gap Audit → Limited Follow-up → Final Adjudicator。

最终未接入主流程。核心发现是题目的复杂度不足以支撑额外的 Agent 层——选项文本直接检索已经覆盖了大部分信息需求，Agent 模式增加的 LLM 调用轮次没有带来足够的证据增量。

## 模型配置

`stages/llm.py` 中的默认值：

```python
DEFAULT_STAGE_MODELS = {
    "adjudicator":          "deepseek-v4-pro",     # 裁判（盲判）
}
DEFAULT_STAGE_REASONING = {
    "adjudicator":          "high",
}
```

复核员和 LLM 二审已砍掉（均为冗余环节：与裁判输入相同，反复判断无增量价值）。
裁判使用 pro 模型（flash 准确率不够）。可通过环境变量覆盖：

```powershell
$env:DS_ADJUDICATOR_MODEL="deepseek-v4-pro"
$env:DS_ADJUDICATOR_REASONING_EFFORT="high"
```

## CE 精排服务器（备选）

默认使用 DeepSeek Flash API 做精排，无需 GPU。如需切回本地 Cross-Encoder：

```powershell
# 启动（需 GPU，6.4GB VRAM）
$env:RERANK_MODEL_PATH="D:/huggingface_models/BAAI/bge-reranker-base"
python rerank_server.py

# 验证
curl -X POST http://localhost:8000/rerank -H "Content-Type: application/json" `
  -d '{"query":"test","documents":["a","b"]}'
```

300 候选分 50 批处理，单次 ~1.7s。并发>7 时 CE 排队导致超时，
推荐并发 7。

## 性能

| 环节 | 耗时 |
|---|---|
| 检索（BGE+BM25+KG+展开） | ~5s |
| Flash 精排（300 候选，API） | ~3s |
| 裁判 LLM（pro+thinking） | 30-60s |
| 后处理（MMR/父块/扩展） | ~2s |
| **单题合计** | **~40-70s** |
| **并发 7 时 45 题** | **~8 分钟** |

瓶颈是裁判 LLM（占 80%+ 时间），并发可有效重叠。

## 术语映射表

考试题目用词与教材句卡原文存在术语落差（如题目说"反制措施"，教材用"应对措施"）。
`retrieval/terminology_map.py` 维护了 题目词 → 教材词 的映射，
在检索前扩展 `must_terms` 以命中教材原文。

### 构建方式

1. 针对考试高频概念，逐一搜索 5199 张句卡的 `knowledge` + `citation` + `chapter_path`
2. 确认该概念在教材中的实际用词及出现频次
3. 建立 题目词 → 教材同义词列表 映射
4. 每个条目 3-8 个关键词

### 当前映射

| 题目用词 | 教材用词 |
|----------|----------|
| 反制措施 | 应对措施、增强尽职调查、点名批评 |
| 监管风险 | 法律风险、声誉风险、刑事和民事处罚 |
| 经济发展疲软 | 经济扭曲和不稳定、制度薄弱、政治不稳定 |
| 没收原则 | 没收、充公、民事没收、犯罪所得 |
| 前台公司 | 空壳公司、空架公司、壳公司 |
| 尽职调查 | CDD、客户尽职调查、KYC |
| 增强尽职 | EDD、强化尽职调查 |
| 可疑活动报告 | SAR、可疑交易报告、STR |

### 维护

- 新增概念前须查 `cards_v6_sentence.json` 确认教材用词
- 不含数量词（如 30天/90天/120天）
- 修改后无需重建 BGE/BM25 缓存（仅影响 exact_phrase）

## 数据模型

| 层级 | 对应 WeKnora | 来源 | 建索引 |
|---|---|---|---|
| 父块 | parent_text Chunk | H4 节全部句卡拼接 | 不建索引 |
| 子块 | Chunk | cards_v6_sentence.json (5199张) | BGE+BM25 |
| 兄弟链 | PreChunkID/NextChunkID | chapter_path 内排序链接 | — |

Embedding 格式：`KNOWLEDGE:{knowledge} CITATION:{citation} SECTION:{H4标题}`

## Plan B：答案知情证据定位

盲判失败不一定等于缺卡——有时卡在候选池里，裁判漏看了。Plan B 做两件事：**扩大池 + 反向精读**。

### 两轨分工

| | 主轨（盲判） | Plan B（答案知情） |
|---|---|---|
| 触发条件 | 默认 | `--plan-b` 手动开启，`final_answer ≠ answer_key` |
| 看答案？ | 否 | **是** |
| 候选池 | 标准检索 | 标准池 + 针对不一致选项独立扩池 |
| 任务 | 判断对错 + 找证据 | 已知答案，在扩池中反向定位证据 |
| 模型 | pro + reasoning_effort=high | flash + reasoning_effort=high |
| 结果 | 改写最终答案 | **追加**，不改原裁判结果 |
| 输出 | `pipeline.explain_options` | `pipeline.plan_b` + JSONL `plan_b_*` 字段 |

### 流程

```text
AI ≠ 题库答案
  → Step 1: 识别不一致选项
       漏选（key有AI没有）→ 找支持证据
       误选（AI有key没有）→ 找反驳证据
  → Step 2: 扩池（plan_b.py: expand_pool_for_plan_b）
       对每个不一致选项独立检索（BGE+BM25+KG）
       window=5（标准3）、KG阈值×0.8
  → Step 3: 合并扩池+原池 → flash+high 反向精读
       prompt 包含：题库答案 + 裁判原判 + 扩池候选（最多50张）
  → Step 4: 写入 pipeline.plan_b（独立字段）
       - evidence_found / recommend_override / still_insufficient
       - option_analysis: plan_b_judgement + evidence_cards + new_card_ids
       - 同步写入 JSONL（plan_b_* 前缀字段）
```

### 实测结果（前 20 错题）

| 指标 | 数值 |
|---|---|
| Plan B 修复 | 6/16（38%） |
| 无法修复（真缺卡） | 7/16（44%） |
| 部分修复 | 3/16（19%） |

- Plan B **不撒谎**：找不到证据时诚实标 insufficient，不会因为知道答案就编造
- 修复的题多数 `new_card_count=0`——不是真找到了新卡，而是把裁判漏读的卡重新解读
- 真正缺卡的题（retrieval gap），扩池后仍然没有，Plan B 也修不了

### CLI

```powershell
# 默认关闭，需手动开启
python .\run_bindings.py --ids 2.1_10 --plan-b --force

# 对单个错题使用：教师需要时手动开启
```

### 建议

不做批量跑。教师对个别错题需要补证据时，手动 `--plan-b` 跑那一道题即可。

## 已知局限

1. **句卡粒度**：单句 ~50-150 字，BGE 语义信号弱于段落级 chunk
2. **LLM 非确定性**：同一题两次运行裁判可能给出不同结果（过选/误判）
3. **教材缺卡**：题库引用的部分法规细节（如 FinCEN 90 天审查期）不在句卡中
4. **术语落差**：题目和教材用词不一致，手工映射表覆盖有限
5. **单选题多证据冲突**：多个选项都有强有力的直接证据时无法自动判定
6. **盲判不一致率**：全书 ~19.5%（137/702），需 Plan B 反向定位证据
