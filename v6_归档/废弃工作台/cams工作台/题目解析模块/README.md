# 题目解析模块

## 定位

借用「新题解析模块」的 agentic 检索思路，实现**题目与全书句卡的链接**。

- 证据池：`cards_v6_sentence.json`（v6s 全书句卡，5199 张）
- 输入：`教材、答疑记录、习题与参考文献/习题/习题结构化提取/{section}_习题集.md`
- 输出：写回 `cams工作台/data/teaching_assets/question_card_map.json`，作为后续考点/高频考点生成的输入池

与新题解析模块的区别：

| 维度 | 新题解析模块 | 题目解析模块（本模块） |
|---|---|---|
| 场景 | 老师在线粘贴单题 | 批量跑章节题库 |
| 流程 | 拆题→检索→盲判→解析→考点提炼 | 拆题→检索→聚合 |
| LLM 环节 | planner + adjudicator + reviewer + 考点 | 仅 planner（可关） |
| 输出 | outputs/drafts 草稿 | question_card_map.json 正式资产 |
| 目的 | 给老师看解析草稿 | 给考点生成提供匹配池 |

## 目录结构

```
题目解析模块/
├── pipeline/
│   ├── evidence_pool.py     # 薄封装，复用新题解析模块的 AgenticRuntime
│   ├── question_loader.py   # 解析习题结构化提取 md → 统一题目格式
│   ├── match_pipeline.py    # 单题匹配：planner + retrieve_for_option + 聚合
│   └── batch_runner.py      # 批量入口 + 合并写回 question_card_map.json
├── outputs/
│   ├── cache/               # 检索缓存（复用新题解析模块）
│   └── reports/             # 批量匹配报告
└── tests/
    └── test_one_chapter.py  # 单章节端到端验证
```

## 用法

### 1. 单章节验证（推荐先跑）

```powershell
cd cams工作台\题目解析模块
python -m tests.test_one_chapter
```

验证 3.1 章节前 2 题的端到端流程。

### 2. 批量匹配

```powershell
cd cams工作台\题目解析模块

# 单章节
python -m pipeline.batch_runner --sections 3.1

# 多章节
python -m pipeline.batch_runner --sections 3.1 3.2 3.3

# 全教材（第 2/3/4/5 章）
python -m pipeline.batch_runner --all

# 只重跑第二章（用 v6s 重跑，自动迁移旧 v6_b##_N## → v6s_N#####）
python -m pipeline.batch_runner --sections 2.1 2.2 2.3 2.4 2.5 2.6 2.7 2.8

# 快速模式（不调 LLM planner，用 stem+option 作 query）
python -m pipeline.batch_runner --sections 3.1 --no-planner

# dry run（只检索不写回）
python -m pipeline.batch_runner --sections 3.1 --dry-run
```

### 3. 合并策略

- 读旧 `question_card_map.json` 的 mappings
- 新匹配按 `question_id` 覆盖/追加
- 第二章旧映射（`v6_b##_N##`）被重跑后的 `v6s_*` 覆盖，**自动完成 ID 迁移**
- 写回前自动备份原文件逻辑（通过 `.tmp` 原子替换）

## 输出格式

写回 `question_card_map.json`，兼容旧格式并扩展：

```json
{
  "asset_note": "题目级候选考点映射（v6s 全书句卡坐标系）...",
  "mappings": {
    "3.1_1": {
      "knowledge_point": "金融行动特别工作组",
      "num_candidates": 12,
      "matched_card_ids": ["v6s_N00017", "v6s_N00018", ...],
      "match_method": "agentic_v6s_planner",
      "option_evidence": {
        "A": [{"card_id": "v6s_N...", "score": 0.85, "quote": "..."}],
        "B": [...]
      }
    }
  },
  "migrations": [...]
}
```

## 依赖

- 复用 ` cams工作台/新题解析模块/pipeline/evidence_pool.py`（BGE + BM25 + 关系扩展）
- 复用 `题目与kg关系建立流水线（四角色法）/` 下的 `run_agentic_search_experiment`、`run_blind_q212_experiment`、`run_step1`
- 句卡池：`cams工作台/data/teaching_assets/cards_v6_sentence.json`
- DeepSeek API（仅 planner 环节，`--no-planner` 可关闭）

## 验证要点

跑完后检查：
1. `question_card_map.json` 里新章节题目的 `matched_card_ids` 是否都是 `v6s_*`
2. `id_prefix_stats_after_merge` 里 `v6_b` 是否归零（第二章迁移成功）
3. 抽样题目的证据句卡 citation 是否真的跟题干相关
4. `outputs/reports/` 下的报告里 `questions_matched` 占比
