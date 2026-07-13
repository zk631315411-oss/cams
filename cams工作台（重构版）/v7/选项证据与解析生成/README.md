# V7 选项证据与解析生成

本工作区承接 V7 教材知识的检索索引、题库标准化、选项级证据召回、盲判裁判、解析整理和后置分歧审计。

当前重点是 Phase 3~4：把“题干/选项 - 教材 unit - AI 判断 - 参考答案分歧”串成可复核材料。Phase 5~8 的考点生成仍属于后续扩展，不是当前主流程。

## 输入资产

| 资产 | 路径 | 说明 |
|------|------|------|
| V7 双语知识单元 | `../../work/base_units/units/v7_bilingual_units.json` | 4973 个 frozen unit |
| V7 卡适配文件 | `../../work/base_units/units/v7_units_as_cards.json` | 4973 条 card 格式 |
| V7 结构化题库 | `../../../教材、答疑记录、习题与参考文献/习题/v7习题/v7结构化文本/CAMS_v7_questions.jsonl` | 395 道题，含中英答案和解析 |
| V7 知识图谱 | `../知识图谱提取/phases/phase06_kg_views/outputs/kg_retrieval_graph.json` | Phase 4 可选 KG 候选扩展 |
| P5 术语别名索引 | `../知识图谱提取/phases/phase05_terms/outputs/p5c_alias_index.json` | Phase 4 可选术语召回 |

## 工作区结构

```text
选项证据与解析生成/
├── README.md
├── config/                         # 全局配置
├── phase3_index/                   # Phase 3: 检索索引构建
│   ├── build_index.py
│   └── output/index/
├── phase3.5_questions/             # Phase 3.5: 题库标准化与质量分层
│   ├── prepare_questions.py
│   ├── fix_ocr_options.py
│   └── output/
├── phase4_evidence/                # Phase 4: 选项证据召回、盲判与解析
│   ├── README.md
│   ├── scripts/
│   │   ├── retrieval_validation.py
│   │   ├── blind_adjudication.py
│   │   └── generate_evidence_explanations.py
│   └── output/
├── scripts/                        # 辅助质量检查脚本
└── 共享资源/                        # 跨阶段共享资源
```

## 阶段总览

| 阶段 | 目标 | 主要脚本 | 当前状态 |
|------|------|----------|----------|
| Phase 3 | 构建 BM25/BGE 检索索引 | `phase3_index/build_index.py` | 已有产物，可按需重建 |
| Phase 3.5 | 标准化题库、章节映射、风险标注 | `phase3.5_questions/prepare_questions.py` | 已有产物，可按需重建 |
| Phase 3.5 修复 | 修复 OCR/选项结构问题 | `phase3.5_questions/fix_ocr_options.py` | 按题源质量需要执行 |
| Phase 4.0 | 验证检索召回质量 | `phase4_evidence/scripts/retrieval_validation.py` | 可抽样执行 |
| Phase 4.1 | 盲判裁判，生成选项级证据判断 | `phase4_evidence/scripts/blind_adjudication.py` | 当前主入口 |
| Phase 4.x | 解析整理，生成教研可读 Markdown | `phase4_evidence/scripts/generate_evidence_explanations.py` | 后处理 |
| Phase 3.6 | 题目到真实教材 CH01-CH59 的直接相似度候选与人工确认映射 | `phase4_evidence/scripts/chapter_mapping.py` | 已接入 |
| 后置审计 | 比对 AI 答案、中英参考答案和参考解析 | 当前为临时汇总流程 | 待固化脚本 |
| Phase 5~8 | 考点生成与后续生产链路 | 待定 | 后续扩展 |

## 核心数据流

```text
CAMS_v7_questions.jsonl
        ↓
phase3.5_questions/prepare_questions.py
        ↓
phase3.5_questions/output/v7_questions.json

v7_bilingual_units / v7_units_as_cards
        ↓
phase3_index/build_index.py
        ↓
phase3_index/output/index/v7_index_*.pkl

v7_questions.json + v7_index_*.pkl + KG/P5（可选）
        ↓
phase4_evidence/scripts/blind_adjudication.py
        ↓
phase4_evidence/output/<run_name>/questions/q_*.json
        ↓
phase4_evidence/scripts/generate_evidence_explanations.py
        ↓
phase4_evidence/output/<run_name>/explanations/*.md
        ↓
后置审计：AI答案 vs 中文参考答案/英文参考答案/参考解析
```

## Phase 4 运行口径

Phase 4 的主裁判脚本是 `phase4_evidence/scripts/blind_adjudication.py`，不是旧规划中的 `run_bindings_v7.py`。

盲判裁判会执行：

1. 加载标准化题库和 Phase 3 索引。
2. 通过 BGE、中文 BM25、英文 BM25 检索候选 unit。
3. 可选启用 P5 术语别名召回。
4. 可选启用 KG，从直接命中的 seed unit 扩展同考点、同节、同章或跨章相邻考点的候选 unit。
5. 调用 LLM，在不提供参考答案的前提下判断每个选项。
6. 执行机械校验，检查 unit_id 是否真实、是否来自候选池、证据卡结构是否合规。
7. 输出每题 JSON、盲判 JSONL 和盲判报告。

解析整理脚本 `generate_evidence_explanations.py` 读取盲判产物，生成教研可读 Markdown。解析阶段的设计目标是不重新判题；裁判答案必须以盲判 JSON 中的 `predicted_answer` 为准。

## 典型命令

```powershell
# 构建检索索引
python phase3_index/build_index.py

# 标准化题库
python phase3.5_questions/prepare_questions.py

# 单题盲判，启用 KG/P5
python phase4_evidence/scripts/blind_adjudication.py --question-id v7_q_000009 --concurrency 1 --enable-kg --enable-p5 --model deepseek-v4-pro

# 对指定输出目录生成解析，并写回每题 JSON
python phase4_evidence/scripts/generate_evidence_explanations.py --output-dir phase4_evidence/output/kg_p5_norm_first50_c30 --limit 0 --concurrency 30 --model deepseek-v4-pro --write-back
```

注意：`blind_adjudication.py --limit N` 是脚本抽样参数，当前默认取 `manual_reviewed` 题目中的前 N 题，不代表自然题号前 N 题。若要跑自然题号前 50 题，应显式传入 `--question-id v7_q_000001 ... --question-id v7_q_000050`，或另行封装批量调度脚本。

## 关键约束

1. 盲判阶段不读取参考答案。题库参考答案和参考解析只用于后置审计与分歧诊断。
2. KG 与 P5 只用于扩展候选证据池，不直接作为答案依据。
3. 裁判答案以 `blind_adjudication.py` 输出的 `predicted_answer` 为准；解析阶段不得覆盖裁判答案。
4. 机械校验不等同于语义蕴含校验。对象错配、条件跳跃、OCR/选项边界错位等问题仍需后续 verifier 或人工复核。
5. 后置参考答案审计目前尚未固化为正式脚本，现有 `phase4_evidence/output/总输出/` 下的审计文件是临时汇总产物。

## 与 v6 的关键差异

| 维度 | v6 | v7 |
|------|----|----|
| 证据单元 | 句卡 `v6s_N*` | 教材 unit `v7u_N*` |
| 检索 | 以中文为主 | 中英混合：中文 BM25、英文 BM25、BGE-M3 |
| 证据锚点 | 中文 citation | 英文 `en_quote` + 中文 `knowledge_zh` 展示 |
| KG 使用 | 旧 KG 导航 | P6 KG retrieval graph 作为候选扩展 |
| 参考答案 | 可作评估 | 只作后置审计，不进入裁判 prompt |

## 当前已知限制

1. 同一题多次运行可能出现答案波动，需要补充跨运行一致性检测。
2. 当前校验只能防止 unit_id 幻觉，不能证明证据真正支持选项语义。
3. 解析整理脚本仍调用 LLM 生成文字，因此必须以 `predicted_answer` 作为唯一裁判答案来源。
4. 题库中存在中英答案冲突、参考解析错位、OCR 选项边界问题，需要在后置审计中保留风险标记。
