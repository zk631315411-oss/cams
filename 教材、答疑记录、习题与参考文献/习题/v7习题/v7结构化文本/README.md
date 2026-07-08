# CAMS v7 structured text

Source workbook:
- `..\CAMS_v7题库_中英对照_v8精修版.xlsx`

Files:
- `CAMS_v7_questions.jsonl`: primary machine-readable file, one question per line.
- `CAMS_v7_questions.json`: same records as one JSON array.
- `CAMS_v7_questions.csv`: spreadsheet/database import version.
- `CAMS_v7_questions.md`: human-readable browse version.
- `CAMS_v7_questions.schema.json`: JSON Schema for one question record.
- `validation_report.txt`: export validation summary.

Important fields:
- `raw_question_cn` / `raw_question_en`: complete question text from the final Excel. Use these as the safest source text.
- `stem_cn` / `stem_en`: best-effort parsed question stem.
- `options_cn` / `options_en`: best-effort parsed options.
- `parse_status`: `ok` means parsed options are structurally usable; `option_parse_low_confidence` means OCR option labels were missing, shifted, or too ambiguous, so downstream code should fall back to `raw_question_*`.
- `answer_final`: normalized answer array.
- `risk_flags`: carried over from the v8 manual-review sheet.

The export does not re-OCR or re-translate. It structures the final reviewed workbook while preserving the original reviewed text.
