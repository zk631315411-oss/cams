# CAMS v7 cleaned question bank

This directory now mirrors the Phase 3.5 cleaned v7 question bank used by the v7 option-evidence and explanation pipeline.

Canonical cleaned source:
- `..\..\..\..\cams工作台（重构版）\v7\选项证据与解析生成\phase3.5_questions\output\v7_questions.json`

Original workbook source:
- `..\CAMS_v7题库_中英对照_精修版.xlsx`

Files:
- `CAMS_v7_questions.json`: canonical cleaned JSON wrapper with `schema_version`, `generated_at`, `total_items`, and `items`.
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
- The v7 evidence pipeline reads the Phase 3.5 cleaned file directly. This directory is a synchronized asset copy so that the question-bank folder and the runtime pipeline use the same cleaned question content.
