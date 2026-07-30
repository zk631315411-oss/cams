# CAMS V6 -> V7 研发与内容交付仓库

本仓库保存 V6 到 V7 的教材处理、证据检索、题目盲判、解析生产、质量复核、软件内容导出及研发记录。它是研发与内容资产仓库，不是正式工作台应用仓库。

正式工作台位于本机同级目录 `D:/守正公司工作区/cams考试工作台（正式版）/`。该应用拥有独立的 `frontend/`、`backend/`、`data/`、`releases/` 和运行说明；本仓库内的 `frontend/`、`workbench-v2/` 均为历史原型。

## 交接入口

- [项目交接说明](项目交接/README.md)
- [V6 到 V7 研发总结](项目交接/V6到V7研发总结.md)
- [正式资产与 SOP 索引](项目交接/正式资产与SOP索引.md)
- [清理记录](项目交接/清理记录.md)

## 当前正式成果

- `cams工作台（重构版）/v7/选项证据与解析生成/phase3.5_questions/output/v7_questions.json`：唯一正式的 395 题结构化母版。
- `cams工作台（重构版）/v7/work/base_units/units/`：4,973 个冻结的 V7 双语知识单元，正式证据锚点为 `v7u_N*`。
- `cams工作台（重构版）/v7/选项证据与解析生成/phase4_evidence/output/questions/`：395 题盲判、选项分析和证据数据。
- `cams工作台（重构版）/v7/选项证据与解析生成/phase4_evidence/output/explanations/`：395 题教研解析母版。
- `cams工作台（重构版）/v7/选项证据与解析生成/phase4_evidence/output/software_export/sections/`：面向题库软件的 63 个小节交付文件及 DOCX。
- `题库解析SOP_DOCX/`：面向运营和交接的正式 SOP 文档。

上述产物中，`output/explanations/` 与 `output/software_export/` 存在尚未提交的终审修订，应按当前工作区内容处理，不能用旧提交覆盖。

题目的最终章节归属以 `software_export/sections/p*-ch*-h*.md` 中的实际小节分配和 `software_export/export_results.json` 为准。历史章节相似度映射与 Agent 映射只用于研发追溯。

## 历史边界

- `v6_归档/`：只读追溯档案，不作为 V7 正式教材依据。
- `cams工作台（重构版）/frontend/`、`cams工作台（重构版）/workbench-v2/`：历史前端与审核原型，不是当前交付主线。
- `教材、答疑记录、习题与参考文献/习题/v7习题/v7结构化文本/`：题源与派生格式快照，不是正式题库母版。
- `cams工作台（重构版）/tools/考点生成/`、`cams工作台（重构版）/tools/知识图谱/提取/`：V6 研究 SOP，不迁移为 V7 正式依据。
- V7 正式证据只能引用真实 `v7u_N*`；V6 的 `v6s_N*` 仅可用于历史核对。

## 开始工作

新教材、新题库按 [新教材新题库解析撰写 SOP](新教材新题库解析撰写SOP.md) 执行；在现有 V7 题库增加新题按 [新题加入处理 SOP](新题加入处理SOP.md) 执行。两条流程的选择规则见 [解析生产链路总览](重构版解析生产链路总结SOP.md)。
