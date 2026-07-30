# Phase 4：盲判、证据与解析

Phase 4 在不向裁判提供参考答案的前提下检索 V7 教材单元、判断选项、绑定证据，并生成教研解析和软件导出。

## 当前入口

| 目录/脚本 | 职责 |
|---|---|
| `盲判流程/blind_adjudication.py` | 检索、LLM 盲判、证据卡、机械校验和逐题 JSON |
| `解析撰写/generate_evidence_explanations.py` | 基于盲判结果生成解析并写回结构化数据 |
| `解析撰写/export_software_explanations.py` | 导出 `p*-ch*-h*` 软件小节 |
| `质量审查/review_check.py` | 机械复查 |
| `质量审查/quality_review.py` | LLM 质量复核 |
| `md-to-docx/` | 软件小节 Markdown 转 DOCX |

旧文档曾引用的 `scripts/retrieval_validation.py`、`题库章节映射/chapter_mapping.py` 和 `导出为docx/` 已不存在或归档，不是当前入口。

## 正式输出

```text
output/
├── questions/q_v7_q_*.json                    # 395 题证据与盲判母版
├── explanations/v7_q_*.md                    # 395 题解析母版
├── software_export/
│   ├── sections/p*-ch*-h*.md                  # 63 个正式软件小节
│   ├── sections/docx/*.docx                   # 63 个软件 DOCX
│   └── export_results.json                    # 395 题全量分配清单
├── docx_bilingual/*.docx                      # 63 个双语 DOCX
├── quality_reviews/                           # 过程质量报告
├── blind_judgment_results.jsonl               # 最后一次局部运行，仅 35 条
└── blind_judgment_report.md                    # 对应局部运行报告
```

`output/explanations_export/` 是旧的 250 题导出，不是当前解析母版。现有质量报告早于部分终审修改，不得作为当前 395 题最终验收证明。

## 章节分配

正式软件章节归属以 `software_export/sections/p*-ch*-h*.md` 和 `export_results.json` 为准。`题库章节映射/数据/` 中的语义相似度映射和 Agent 映射均为历史研究资料，不再决定正式小节。

## 安全运行规则

1. 不直接覆盖根 `output/`；调试必须使用新的显式输出目录。
2. 盲判阶段不读取参考答案。
3. KG 与 P5 只用于候选扩展，正式证据必须是 `v7u_N*`。
4. 解析阶段不得静默覆盖盲判答案；人工终审修改必须保留版本差异。
5. 任何“需复核题数”都应从当前文件重新生成，不能沿用 91 或 148 的历史统计。
