# Phase 4: v7 题目证据生成

Phase 4 负责在不向模型提供参考答案的前提下，对 v7 题目选项召回教材证据，生成可审计的选项级判断、证据材料和教研解析。

它不是题库答案清洗阶段，也不是最终人工定稿阶段；它的核心价值是把“题干/选项 - 教材 unit - AI 判断 - 后置参考答案分歧”串成可复核材料。

## 子阶段

| 子阶段 | 脚本 | 角色 | 主要产物 |
|--------|------|------|----------|
| Phase 4.0 检索质量验证 | `scripts/retrieval_validation.py` | 检索验证 | 检索验证 JSONL、检索质量报告 |
| Phase 4.1 盲判裁判 | `scripts/blind_adjudication.py` | 主裁判 | 每题 `q_*.json`、盲判汇总、盲判报告 |
| Phase 4.x 解析整理 | `scripts/generate_evidence_explanations.py` | 教研助理 | 每题 Markdown 解析、`generated_explanation` |
| 后置审计 | 当前为临时汇总流程 | 分歧诊断 | AI-参考答案审计 JSON/JSONL/CSV/MD |

## 输入资产

- `phase3_index/output/index/`：Phase 3 构建的 BM25/BGE 检索索引，包含 unit lookup。
- `phase3.5_questions/output/v7_questions.json`：Phase 3.5 标准化后的 v7 题库。
- `../../work/base_units/units/`：v7 frozen unit 原始来源。
- `../../知识图谱提取/phases/phase06_kg_views/outputs/kg_retrieval_graph.json`：可选 KG 候选扩展图谱。
- `../../知识图谱提取/phases/phase05_terms/outputs/p5c_alias_index.json`：可选 P5 术语别名索引。

## 核心数据流

```text
v7_questions.json + phase3_index
        ↓
scripts/blind_adjudication.py
        ↓
output/<run_name>/questions/q_*.json
        ↓
scripts/generate_evidence_explanations.py
        ↓
output/<run_name>/explanations/*.md
        ↓
后置审计：AI答案 vs 中文参考答案/英文参考答案/参考解析
```

`blind_adjudication.py` 是当前 Phase 4 的主入口。它加载题库和索引，执行 BGE、中文 BM25、英文 BM25、P5 术语别名召回，并可通过 KG 从直接命中的 seed unit 扩展同考点、同节、同章或跨章相邻考点的候选 unit。随后脚本调用 LLM 进行盲判，输出 `predicted_answer` 和各选项的 `option_analysis`。

`generate_evidence_explanations.py` 是后处理脚本。它读取盲判产出的 `q_*.json`，把已有裁判结论、证据卡和 unit 原文整理成教研可读解析。解析阶段的设计目标是不重新判题；裁判答案必须以 `blind_adjudication.py` 的 `predicted_answer` 为准。

## 典型使用

```powershell
# 单题盲判
python scripts/blind_adjudication.py --question-id v7_q_000009 --concurrency 1 --enable-kg --enable-p5 --model deepseek-v4-pro

# 对指定输出目录生成解析，并写回每题 JSON
python scripts/generate_evidence_explanations.py --output-dir output/kg_p5_norm_first50_c30 --limit 0 --concurrency 30 --model deepseek-v4-pro --write-back

# 检索质量验证
python scripts/retrieval_validation.py --limit 15
```

注意：`blind_adjudication.py --limit N` 是脚本抽样参数，当前默认取 `manual_reviewed` 题目中的前 N 题，不等同于自然题号前 N 题。若要运行自然题号前 50 题，应显式传入 `--question-id v7_q_000001 ... --question-id v7_q_000050`，或另行封装批量调度脚本。

## 输出口径

每次运行建议写入独立目录，例如：

```text
output/<run_name>/
├── questions/q_v7_q_*.json
├── blind_judgment_results.jsonl
├── blind_judgment_report.md
└── explanations/
    ├── v7_q_*.md
    ├── index.md
    └── generation_results.json
```

后置参考答案审计目前尚未固化为正式脚本，现有 `output/总输出/q001_q020_*`、`output/总输出/q001_q050_*` 是基于盲判结果和 `CAMS_v7_questions.jsonl` 临时汇总生成的结构化对照材料。

## 关键约束

1. 盲判阶段不读取参考答案。题库中的 `answer_cn`、`answer_en`、`answer_final` 和参考解析只用于后置审计与分歧诊断。
2. KG 与 P5 只用于扩展候选证据池，不直接作为答案依据。最终引用必须回到候选 unit 的中英文原文。
3. 裁判答案以 `blind_adjudication.py` 输出的 `predicted_answer` 为准；解析阶段不得覆盖裁判答案。
4. 机械校验只检查 unit_id 是否真实、是否来自候选池、证据卡结构是否合规；它不等同于语义蕴含校验。
5. 当前系统仍缺少跨运行一致性检测和“证据是否真正支持选项”的二次 verifier。对象错配、条件跳跃、题源 OCR 错位等问题仍需进入人工复核或后续校验阶段。
