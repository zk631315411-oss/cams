# 选项证据生成

为正式题库的每道题、每个选项找到教材句卡依据，输出题目-选项-句卡绑定结果。

## 当前系统

**主入口**：`新题解析模块复用/run_bindings.py`

WeKnora 式 RAG 检索 + 盲判裁判。流程：

```
题目 → 检索(BGE+BM25+KG+扩展+Flash精排+MMR+父块替换)
     → 盲判裁判(pro+high)
     → 答案确定(规则)
     → 输出每题JSON + JSONL绑表
```

全量 703 题，题目级一致率 80.5%。

```powershell
cd "新题解析模块复用"
python run_bindings.py --limit 20 --concurrency 7   # 跑20题
python run_bindings.py --ids 2.1_15 --force          # 单题重跑
python run_bindings.py --ids 2.1_15 --plan-b --force # 启用Plan B补证据
```

详见 `新题解析模块复用/README.md`。

## 历史系统（已废弃）

### run_step1.py

四角色法主流程（AI#1 关联分析 → AI#2 主张提取 → BGE 检索 → AI#3 裁判）。被新管线替代，仅保留在 `archive/` 中。

### run_step2_option_mapping.py

格式化 + 验证 step1 输出。新管线内置了绑定表导出，不再需要。

## 数据流（当前）

```
习题结构化 MD (720题)           cards_v6_sentence.json (5199张)
        │                              │
        ▼                              ▼
  新题解析模块复用/run_bindings.py ─── kg_data.json (知识图谱)
        │
        ▼
  output/questions/q_{id}.json         (每题完整pipeline过程)
  output/question_option_card_bindings.jsonl  (选项级绑定表)
```

## 配置

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DS_ADJUDICATOR_MODEL` | `deepseek-v4-pro` | 裁判模型 |
| `DS_ADJUDICATOR_REASONING_EFFORT` | `high` | 裁判思维强度 |
| `DEEPSEEK_API_KEY` | — | API Key |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | API 地址 |
