# CAMS V7 题源与派生格式快照

本目录保存题源清洗后的 JSON、JSONL、CSV 和 Markdown 辅助格式，不是正式题库母版，也不保证与后续终审内容实时同步。

唯一正式题库母版：
- `..\..\..\..\cams工作台（重构版）\v7\选项证据与解析生成\phase3.5_questions\output\v7_questions.json`

2026-07-30 交接核验发现，本目录 JSON 与正式母版虽均为 395 题，但存在题干、选项和 28 题答案差异。因此本目录只能作为来源与派生快照，禁止反向覆盖 Phase 3.5 正式母版。

Original workbook source:
- `..\CAMS_v7题库_中英对照_精修版.xlsx`

Files:
- `CAMS_v7_questions.json`: 历史清洗 JSON wrapper，含 `schema_version`、`generated_at`、`total_items` 和 `items`。
- `CAMS_v7_questions.jsonl`: one cleaned question item per line.
- `CAMS_v7_questions.csv`: flattened spreadsheet/database import version.
- `CAMS_v7_questions.md`: human-readable browse version.
- `CAMS_v7_questions.schema.json`: JSON Schema for the cleaned wrapper and question item.
- `validation_report.txt`: cleaned export validation summary.

Important fields:
- `question_id`: normalized id, e.g. `v7_q_000001`.
- `source_question_id`: original question id, e.g. `CAMS-V7-0001`.
- `chapter_code`, `chapter_path_zh`, `chapter_path_en`: chapter mapping used by downstream retrieval and audit.
- `question_type`: `single`, `multiple`, or `unknown`.
- `stem` / `stem_en`: cleaned Chinese and English stems.
- `options` / `options_en`: cleaned option dictionaries keyed by `A`, `B`, `C`, etc.
- `answer`: normalized reference answer array.
- `answer_source`: answer provenance such as `official` or `unknown`.
- `tier`: quality tier such as `clean` or `answer_conflict`.
- `risk_flags`: OCR, manual-review, or answer-conflict markers preserved for audit.
- `raw_question_en`: original English OCR/source text retained when available.

Operational note:
- V7 evidence pipeline 只读取 Phase 3.5 正式母版。本目录不得作为运行输入，除非先完成从正式母版的受控同步和差异验收。
