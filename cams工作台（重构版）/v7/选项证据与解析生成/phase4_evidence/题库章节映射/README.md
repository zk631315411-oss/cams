# 题库章节映射历史资料

本目录保存两套 395 题章节研究映射：语义相似度 + Agent 审核版，以及只依据题目与章节目录判断的 Agent 版。两者均不再决定正式章节归属。

正式章节归属以 `../output/software_export/sections/p*-ch*-h*.md` 的实际分配和 `../output/software_export/export_results.json` 为准。

- `数据/question_chapter_mappings.jsonl`：旧语义相似度映射。
- `数据/question_chapter_mappings_agent.jsonl`：目录级 Agent 映射。
- `数据/chapter_similarity_candidates*`：候选与审查材料。
- `数据/chapter_batches/`：历史按章批次。

旧 `chapter_mapping.py` 已归档，不是当前生产入口。盲判调试可显式读取历史映射筛题，但正式软件小节不得由该目录反向覆盖。
