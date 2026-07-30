# Phase 4 输出边界

本目录同时保存正式母版与历史过程记录，使用时必须区分：

## 正式保留

- `questions/`：395 题证据、盲判和结构化解析数据。
- `explanations/`：395 份当前解析 Markdown。
- `software_export/sections/`：63 个 `p*-ch*-h*` 正式软件小节及 63 个 DOCX。
- `software_export/export_results.json`：395 题全量分配清单。
- `docx_bilingual/`：63 个双语 DOCX。

## 过程资料

- `explanations_export/`：旧 250 题导出，不是当前母版。
- `explanations/generation_results.json`：旧生成批次的辅助清单，当前为异常的 PowerShell/.NET 序列化形态且只记录 394 题；不得用于判断正式解析覆盖率。正式覆盖率以 395 份 `v7_q_*.md` 和对应题目 ID 集合为准。
- `quality_reviews/` 及质量报告：生成时间早于部分终审，仅供追溯。
- 根 `blind_judgment_results.jsonl` 和报告：最后一次局部运行只有 35 题，不是全量清单。
- `docx/`、`docx_en/`：其他格式导出或空目录。

最终章节归属以 `software_export/sections/` 的实际文件和 `export_results.json` 为准。禁止用任何过程目录反向覆盖正式保留项。

当前 395 个软件题块中，389 个旧“教材章节”展示字段仍为“未映射”，3 个缺少该字段，只有 3 个写有具体教材章节。该字段不承担软件小节分配职责，也不能据此否定题目所在的 `p*-ch*-h*` 文件；若后续需要补齐教材章节展示，应从正式 `v7u_N*` 证据锚点重新生成，不能用旧章节映射回填。
