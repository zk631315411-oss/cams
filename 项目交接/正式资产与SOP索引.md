# 正式资产与 SOP 索引

## 一、资产分级

### A. 原始来源，永久保留

| 资产 | 路径 | 说明 |
|---|---|---|
| V7 教材及提取文本 | `教材、答疑记录、习题与参考文献/教材原文/v7/` | PDF、MinerU 中英文 MD 等原始依据 |
| V7 题库来源与派生快照 | `教材、答疑记录、习题与参考文献/习题/v7习题/v7结构化文本/` | JSONL、JSON、CSV、Markdown 等辅助格式；不是正式母版 |
| V6 历史资产 | `v6_归档/` | 只读追溯，不作为 V7 正式依据 |

### B. V7 正式底座，永久保留

| 资产 | 路径 | 当前口径 |
|---|---|---:|
| 冻结双语知识单元 | `cams工作台（重构版）/v7/work/base_units/units/v7_bilingual_units.json` | 4,973 |
| 兼容卡格式 | `cams工作台（重构版）/v7/work/base_units/units/v7_units_as_cards.json` | 4,973 |
| 冻结清单 | `cams工作台（重构版）/v7/work/base_units/units/unit_freeze_manifest.json` | 记录冻结规则和映射 |
| 排除/待复核清单 | `cams工作台（重构版）/v7/work/base_units/units/excluded_or_review_manifest.json` | 10 项 |
| 检索索引 | `cams工作台（重构版）/v7/选项证据与解析生成/phase3_index/output/index/` | BM25/BGE/lookup |
| V7 知识图谱 | `cams工作台（重构版）/v7/知识图谱提取/phases/phase06_kg_views/outputs/` | 检索增强，不是直接证据 |

### C. 题目生产母版，永久保留

| 资产 | 路径 | 当前口径 |
|---|---|---:|
| 标准化题库 | `cams工作台（重构版）/v7/选项证据与解析生成/phase3.5_questions/output/v7_questions.json` | 395 |
| 单题盲判与证据 | `cams工作台（重构版）/v7/选项证据与解析生成/phase4_evidence/output/questions/` | 395 JSON |
| 单题解析母版 | `cams工作台（重构版）/v7/选项证据与解析生成/phase4_evidence/output/explanations/` | 395 MD |

`questions/` 与 `explanations/` 是正式内容，不因已有软件导出而删除。前者保留结构化判断与证据，后者保留人读和终审文本。

题目的正式章节归属以 `software_export/sections/p*-ch*-h*.md` 和 `software_export/export_results.json` 为准。`题库章节映射/数据/` 下的旧映射和 Agent 映射均为过程资料。

注意：软件小节内保留的旧“教材章节”展示字段大多仍为“未映射”，它不是本次软件小节归属的来源。接手方不得用该字段或 `explanations/generation_results.json` 重新判定覆盖数；正式覆盖以 395 份题目 JSON、395 份解析 MD、63 个 `p*-ch*-h*` 文件和 `export_results.json` 为准。

### D. 正式交付文件，永久保留

| 资产 | 路径 | 当前口径 |
|---|---|---:|
| 软件小节 Markdown | `phase4_evidence/output/software_export/sections/*.md` | 63 |
| 软件小节 DOCX | `phase4_evidence/output/software_export/sections/docx/*.docx` | 63 |
| 双语小节 DOCX | `phase4_evidence/output/docx_bilingual/` | 63 |
| 导出清单 | `phase4_evidence/output/software_export/export_results.json` | 395 题全部导出 |
| 运营与 SOP 文档 | `题库解析SOP_DOCX/` | 3 份正式 DOCX 及配图 |

上表中的相对路径均位于 `cams工作台（重构版）/v7/选项证据与解析生成/`，除非单独说明。

### E. 历史原型，保留但不作为正式入口

- `cams工作台（重构版）/frontend/`
- `cams工作台（重构版）/workbench-v2/`
- `v6_归档/废弃工作台/`

这些目录可用于追溯交互和产品思路，但不能提供正式题目、证据或解析。

### F. 正式应用，同仓维护与完整快照

正式应用可维护副本位于本仓库 `cams考试工作台（正式版）/`。源码、文档、测试、395 题档案和冻结基础设施按普通 Git 文件维护；`.venv`、本地模型、独立 Git 历史和全部本机运行文件由 `项目交接/正式工作台完整快照/` 的 Git LFS 分卷保存。正式应用的启动、数据档案、审核状态和发布包以其自身 README 为准。

## 二、SOP 路由

| 场景 | 先读 | 继续执行 |
|---|---|---|
| 判断任务属于重建还是增量 | `重构版解析生产链路总结SOP.md` | 选择下列一条流程 |
| 新教材、新题库 | `新教材新题库解析撰写SOP.md` | 从教材验收到整批解析交付 |
| 现有 V7 题库增加新题 | `新题加入处理SOP.md` | 来源登记、结构化、盲判、核证、审核、增量发布 |
| 理解当前脚本限制 | `新题加入技术执行与现状限制.md` | 核对覆盖风险和未自动化门禁 |
| 运营使用和责任分工 | `CAMS题库项目说明与运营使用指南.md` | 按角色和状态推进 |
| 需要 Word 版 | `题库解析SOP_DOCX/` | 使用对应 DOCX，不从临时预览目录取文件 |

## 三、正式生产链

```text
V7 原始 PDF + 中英文 MD
  -> 双语知识单元构建与冻结（4,973 unit）
  -> 检索索引 + KG/P5 候选增强
  -> 题库标准化（395 题）
  -> DS 盲判与选项级证据 JSON
  -> 参考答案后置冲突审计
  -> 解析 Markdown
  -> Codex 核证与人工终审
  -> 软件小节 Markdown / DOCX
  -> 发布清单与上线复核
```

## 四、发布前最低核对

1. 发布题目均有正式题目 ID、当前解析和人工批准记录。
2. 所有教材证据都能回到真实 `v7u_N*`、英文原文和页码。
3. 发布数量与批准清单、软件导出数量一致。
4. 当前质量报告的生成时间晚于本批最后修改时间。
5. DOCX/软件录入后的题干、选项、答案、解析和页码经过实际展示核对。
