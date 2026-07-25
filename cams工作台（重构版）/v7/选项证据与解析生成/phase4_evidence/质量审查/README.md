# 质量审查

## 文件说明

| 文件 | 定位 |
|---|---|
| `review_check.py` | 薄包装。实现已合并到 `解析撰写/s5_explanation_review.py`，从此处 import 供独立运行 |
| `quality_review.py` | LLM 驱动解析质量复核：按五类证据错误模式（语境偷换、主语借代、后合理化、页码幻觉、语气放大）独立审查每题解析 |

## 用法

### 机械合规检查

```bash
cd 质量审查/
python review_check.py --output-dir ../output
python review_check.py --output-dir ../output --quality-review-dir ../output/quality_reviews
python review_check.py --output-dir ../output --question-ids v7_q_000072,v7_q_000089
```

### LLM 质量复核

```bash
cd 质量审查/
python quality_review.py --output-dir ../output --limit 5
python quality_review.py --output-dir ../output --sample-per-chapter 3
```

## 与其他模块的关系

```
质量审查/quality_review.py
  ├── 解析撰写/s1_explanation_data  (load_question_result, get_llm_config, ...)
  ├── 解析撰写/s2_explanation_material  (candidate_by_unit)
  ├── 解析撰写/export_software_explanations  (_load_kg_section_index, ...)
  └── 公共函数/{llm_utils, index}  (call_llm, parse_llm_output, collect_cited_unit_ids)

质量审查/review_check.py → 解析撰写/s5_explanation_review.py  (所有实现在 s5)
```

## 历史

- `quality_review_test.py`（旧版，仅有证据质量检查）已移到 `_attic/`
