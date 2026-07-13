# 题目与 KG 关系建立流水线（四角色法）

## 一句话总览

把"题目、选项、标准答案"与"教材原文句卡"建立可追溯关系，产出选项级教材依据、题目证据绑定和候选考点资产。

当前新题解析模块、学生答疑模块也复用了这里的检索、证据池和 LLM 调用能力，所以本目录的脚本既是"四角色法流水线"，也是整个系统的"公共运行时基础模块"。

## 目录地位

- 当前正式产物：`output/agentic_full_ch2_20260615/`（第二章 179 题）、`output/agentic_patch_2.2_20_20260615/`、`output/step2_full_ch2_20260615/`
- 历史/中间/测试产物已归档到 `历史_中间_测试产物/`，详见该目录下 README
- 脚本名是项目演化过程中留下的工程临时命名，名字和实际作用可能不一致，详见 `脚本说明.md`

## 当前主线脚本

| 脚本 | 人话名称 | 作用 |
|---|---|---|
| `run_step1.py` | 题目证据绑定主入口 / 公共运行时基础模块 | 读取题目、教材句卡、KG 辅助资产；初始化 DeepSeek、BGE、证据池等运行时；提供带标准答案题目的证据绑定流程；提供公共函数（LLM 调用、答案归一化、状态分类、质量统计）。新题解析、学生答疑模块会 import 它。 |
| `run_agentic_search_experiment.py` | Agentic 多路检索与证据裁判核心模块 | 根据题目和选项生成检索计划；混合召回教材句卡（BGE、关键词、短语、相邻句卡、关系扩展、可选 LLM 句卡扫描）；对候选证据做裁判，输出选项级证据状态和教材依据。可独立 CLI 运行。 |
| `run_blind_q212_experiment.py` | 无标准答案盲判流程参考模块 | 探索"不给标准答案，模型自己判断答案"的流程。新题解析模块借用了里面的盲判思路和部分辅助函数（`build_blind_planner_prompt`、`normalize_blind_plan`、`build_blind_adjudicator_prompt`、`leakage_check`、`sanitize_blind_result`）。 |
| `run_parallel_agentic_batch.py` | 批量跑题调度脚本 | 按题目批量调用 agentic 流程；支持小并发、分组运行、断点续跑和报告输出。通过 subprocess 调用 `run_agentic_search_experiment.py`。 |
| `run_step2_option_mapping.py` | 选项级教材依据映射生成器 | 读取每题的 agentic 结果，生成题目、选项、教材句卡之间的结构化映射，产出 `question_option_card_map.json`、`card_option_question_map.json`、`stats.json`。可写回前端 `cams工作台/data/option_evidence_map.json`。 |

数据构建脚本（`build_v6_sentence_cards.py`、`build_ch2_sentence_cards.py`、`build_v6_except_ch2_sentence_cards.py`、`build_combined_evidence_pool.py`、`build_exam_point_mapping.py`）和审查脚本（`audit_option_mapping.py`）的说明见 `脚本说明.md`。

## 当前最新入口与推荐运行方式

### 单题/小批量

```powershell
python run_step1.py --retrieval agentic --ids 2.1_1 2.1_2 2.1_3 --force --card-scan correct
python run_step1.py --retrieval agentic --limit 5 --force --card-scan correct
```

`run_step1.py` 在 agentic 模式下会在同进程内 import `run_agentic_search_experiment` 执行。默认输出到 `output/step1_ai_responses/`，无 `--output-dir` 参数。

### 批量并行（推荐用于大规模重跑或扩展章节）

```powershell
python run_parallel_agentic_batch.py --output-dir output/agentic_full_ch2_20260615 --max-workers 2 --target all-questions
```

`run_parallel_agentic_batch.py` 通过 subprocess 调用 `run_agentic_search_experiment.py`，可用 `--output-dir` 自定义输出目录。`--target` 支持 `weak / not-fullbook / no-teacher-hints / missing-formal / all-existing / all-questions`。

### 选项级证据映射

```powershell
python run_step2_option_mapping.py --step1-dir output/agentic_full_ch2_20260615 --output-dir output/step2_full_ch2_20260615 --write-frontend
```

`--write-frontend` 会把产物写回 `cams工作台/data/option_evidence_map.json`。

## 关键参数（README 此前未记录）

| 参数 | 取值 | 作用 |
|---|---|---|
| `--retrieval` | `baseline` / `agentic` | `baseline` 是旧的 AI#1/AI#2/BGE 章节召回流程；`agentic` 是推荐模式，按选项生成检索计划，多路召回 + 证据裁判。 |
| `--evidence-scope` | `ch2` / `v6-sentence` / `v6-except-ch2` / `ch2-plus-v6-except` | 证据池范围。`v6-sentence` 是全书句卡池（约 5199 张），是支持跨章节证据召回的关键参数。`run_step1.py` 默认 `ch2`；新题解析模块默认 `v6-sentence`。 |
| `--teacher-hints` | flag | 把 `question.explanation` 当检索提示用，不当教材证据。 |
| `--card-scan` | `off` / `correct` / ... | 是否启用 LLM 句卡扫描补召回。 |
| `--card-scan-chunk-size` | int | LLM 句卡扫描的批大小。 |
| `--ids` / `--limit` | | 题目选择。脚本不硬编码章节过滤，questions.json 里有什么题就跑什么题。 |
| `--force` | flag | 强制重跑已存在结果。 |
| `--skip-existing` | flag（`run_parallel_agentic_batch.py`） | 跳过已存在结果，用于断点续跑。 |

## answered 状态口径

`answered` 的口径是：标准答案中的每一个正确选项都有 direct 教材句卡证据。多选题只要任一正确选项缺 direct，就必须是 `partial` 并标教研复核。其他状态：`evidence_insufficient`（BGE 搜到 0 条证据，或 AI#3 无法基于证据做判断）、`ai1_failed` / `ai2_failed` / `ai3_failed`（某角色调用失败）。

## 输入数据依赖

`run_step1.py` / `run_agentic_search_experiment.py` 读取：

- 题目：`cams工作台/data/questions.json`（`DATA = BASE.parent / "cams工作台" / "data"`）
- 句卡证据池（按 `--evidence-scope` 切换）：
  - `ch2` → `cams工作台/data/cards_ch2.json`
  - `v6-sentence` → `cams工作台/data/cards_v6_sentence.json`（全书 5199 张句卡）
  - `v6-except-ch2` → `cams工作台/data/cards_v6_except_ch2_sentence.json`
  - `ch2-plus-v6-except` → `cams工作台/data/cards_ch2_plus_v6_except_ch2_sentence.json`
- KG 资产：`cams工作台/data/agentic_search_eval_v2/kg/` 下的 `sections.json`、`edges.json`、`card_section_map.json`
- 卡片关系：`cams工作台/data/card_relations.json`

注意 `run_parallel_agentic_batch.py` 自己读 `题目与kg关系建立流水线（四角色法）/数据/data/questions.json`（路径不同），但子进程实际跑的是 `run_agentic_search_experiment.py`，后者仍读 `cams工作台/data/questions.json`。两个文件目前内容一致，但这是潜在不一致风险点。

## 与新题解析 / 学生答疑模块的关系

`cams工作台/新题解析模块/pipeline/evidence_pool.py` 和 `run_pipeline.py` 直接 import 本目录的 `run_step1`、`run_agentic_search_experiment`、`run_blind_q212_experiment`，复用其 Runtime、检索函数、盲判 prompt builder 等。三个关键差异：

1. 新题解析不给标准答案（教师粘贴新题文本），用 `run_blind_q212_experiment` 的盲判 prompt；本目录四角色法 agentic 模式是带标准答案的证据绑定。
2. 新题解析不加载 `questions.json`（新题不在题库）。
3. 新题解析默认证据池是全书 `v6-sentence`，并加了 BGE/BM25 的 pickle 缓存。

**所以本目录的核心脚本不能随便重命名或移动**，否则会破坏新题解析模块。学生答疑模块（agentic 版）同样复用了这里的检索能力。

## 数据现状与扩展路径

### 当前覆盖

- `cams工作台/data/questions.json`：179 题，全部是第二章（2.1~2.8）
- `cams工作台/data/teaching_assets/option_evidence_map.json`：仅第二章选项级证据
- `cams工作台/data/teaching_assets/question_card_map.json`：179 题，仅第二章
- `cams工作台/data/teaching_assets/cards_v6_sentence.json`：5199 张句卡，**全书已覆盖**

### 扩展到第 3/4/5/6 章

脚本本身不硬编码章节过滤，可直接处理新章节题目。流程：

1. 把 `教材、答疑记录、习题与参考文献/CAMS物料/结构化提取/*_习题集.md` 解析进 `cams工作台/data/questions.json`（用 `cams工作台/data_pipeline/parse_questions.py`，需扩展以支持新格式）。
2. 跑 `run_parallel_agentic_batch.py --target all-questions --evidence-scope v6-sentence --output-dir output/agentic_full_v6_<日期>`，复用全书句卡池做证据召回。
3. 跑 `run_step2_option_mapping.py --write-frontend`，把选项级证据写回工作台。
4. 跑 `cams工作台/data_pipeline/match_questions.py` 扩展 `question_card_map.json`（bind_qa.py 句卡继承的来源）。

第 6 章题目采用主题式编号（`6.KYC`、`6.人口贩卖` 等），不是 `6.1`/`6.2` 形式。如果 questions.json 的 id 沿用主题式，需要在 section 解析、question_card_map、bind_qa 等环节留意编号规则。

## 铁律

- 旧解析、教研答疑不进入 prompt
- 教材原文 + 卡片全量可用
- 每一步的 LLM 输出驱动下一步
- AI 写不出来的地方标记"证据不足"，不编造
- 每条推理必须可追溯 card_id
- 每次跑完一题立刻写 JSON，防止中断丢失

## 验收目标

教研打开 HTML，每道题按状态分类。绿色题 30 秒审核通过，红色题标记需人工处理。教研的时间从"从零写解析"变成"审核卡片引用是否相关"。

验收维度：可追溯性（100%）、引用相关性（≥70%）、可答率（≥70%）、四角色隔离审计、教研可使用性。

## baseline 模式的四角色法定义（旧流程，仅 `--retrieval baseline` 时适用）

将一次 LLM 调用拆成四个角色接力，形成隔离与校验闭环：

```
题目 + 选项 + 答案
    │
    ▼
AI #1 联想者 ── 自由联想，跨节推测。输出完整分析 + "需要教材验证的事实主张"
    │
    ▼
AI #2 核查员 ── 只看 AI #1 输出。提取可用教材原文验证的具体主张，生成搜索 query
    │
    ▼
BGE 搜索 ── 把 query 编码 → 匹配章节节点 → 拉对应卡片原文
    │
    ▼
AI #3 裁判官 ── 只看题目 + 答案 + BGE 搜到的卡片证据。不看 AI #1 输出
                   基于证据写解析，每句挂 card_id；证据不足时直接标记，不编造
```

**关键约束：AI #3 绝不看 AI #1 的输出。** 这保证了最终解析必须基于教材原文，不能靠模型的训练数据"猜"。

`--retrieval agentic` 推荐模式下，AI#1/AI#2 已被"LLM 搜索规划器 + 多路检索"取代，流程变为：LLM 搜索规划器 → 多路检索（card-level BGE / BM25 / 短语 / 相邻句卡 / 关系扩展 / 可选 LLM 句卡扫描）→ LLM 证据裁判 → 可选 follow-up。隔离原则保留（裁判阶段不看规划阶段的联想输出）。

## 已知限制

- **卡片粒度不够：** 法条级知识（Patriot Act §319(b)、EU AMLD 条款）不在卡片中，这类题会标 evidence_insufficient
- **BGE 术语鸿沟：** 题目用词和教材用词不一致时（"巢状交易" vs "通汇账户"），BGE 有时能跨过有时不能
- **不能替代教研判断：** 教研需审核卡片引用是否相关，这不是"全自动"而是"辅助加速"

## 历史进度记录

| 步骤 | 状态 | 进度 |
|---|---|---|
| 第二章 179 题全量跑完 | 已完成 | `output/agentic_full_ch2_20260615/` 179 题 |
| 第二章选项级证据映射 | 已完成 | `output/step2_full_ch2_20260615/`，已写回 `cams工作台/data/teaching_assets/option_evidence_map.json` |
| 第 3/4/5/6 章扩展 | 待执行 | 待 questions.json 扩展后跑 `--evidence-scope v6-sentence` |

早期"14/179 试跑"记录属于旧 baseline 探索，不作为当前 agentic 模式验收口径。当前验收以 `run_step1.py --retrieval agentic` 输出为准。

## 设计文档

- `README.md`（本文件）：四角色法与 agentic 流水线总说明
- `脚本说明.md`：把脚本名翻译成人话，帮助快速判断哪些是主线、哪些是构建工具、哪些是历史遗留
- `历史_中间_测试产物/README.md`：归档产物说明
