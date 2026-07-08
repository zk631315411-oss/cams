# v8 OCR audit batches

These JSONL files are read-only inputs for sub-agent OCR/readability review.
Each line contains one Chinese-English aligned item with fields: cn.question, cn.answer, cn.analysis, en.question, en.answer, en.analysis, answer_status, pair_risk.
Sub-agents should create report files named report_cnXXX_YYY.jsonl in this directory.
