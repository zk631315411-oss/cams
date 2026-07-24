# v7_review_build — 审核源构建工具

## 职责

从机器产物目录扫描题目 JSON，校验数据完整性，生成可供人工审查的审核源。

## 流程

```
textbook-active.json ──→ 教材 manifest ──→ units.json
                                    │
machine questions/ ──→ 校验 → 计算 machine_hash → 审核源 manifest.json
                                    │
                                    └──→ review-active.json 指针
```

## 输入

| 输入 | 路径 |
|------|------|
| 教材指针 | `frontend/data/releases/v7/textbook-active.json` |
| 教材 manifest | 指针中 `manifest` 字段指向的 JSON |
| 教材 units | manifest 中 `source.units.path` 指向的 JSON |
| 机器产物 | `v7/选项证据与解析生成/phase4_evidence/output/questions/` |

## 输出

| 输出 | 路径 |
|------|------|
| 审核源 | `frontend/data/releases/v7/review-source/{release_id}/` |
| 审核指针 | `frontend/data/releases/v7/review-active.json` |

## 校验规则

1. `question_id` 不重复
2. `options` 非空字典，键为单字符
3. `question_type` 为 `single` / `multi` / `unknown`
4. `candidate_pool` 中 `unit_id` 存在于教材 units
5. `evidence_cards` 中 `support_type` 为 `direct` / `indirect` / `context`
6. `predicted_answer` 选项在 `options` key 中
7. 无 `v6` 标识
8. 每题计算 `machine_hash`（SHA256 of evidence 部分）

校验失败时脚本终止，不生成产物。

## 幂等

目标目录已存在时跳过生成步骤，不覆盖已有数据。
