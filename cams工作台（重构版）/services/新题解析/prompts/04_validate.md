# 质量校验规则

校验由 `run_pipeline.py` Step 5 以纯代码执行，**不调用 LLM**。

## 自动校验项

| # | 检查项 | 通过条件 | 失败/警告 |
|---|--------|----------|-----------|
| 1 | 题干完整性 | stem 非空且 >= 5 字符 | fail（空） / warning（有 parse_warnings） |
| 2 | 选项完整性 | options >= 2 个 | fail |
| 3 | AI 答案范围 | predicted_answer 中每个标签在 options 中 | fail（不在范围） / warning（空） |
| 4 | 每个选项均有解析 | 每个 option_analysis entry 的 explanation 非空 | warning |
| 5 | 引用句卡存在 | evidence_cards 中的 card_id 在 valid_card_ids 中 | fail（幻觉） |
| 6 | 引用在候选内 | evidence_cards 中的 card_id 在检索候选中 | warning |
| 7 | 检索结果 | 至少 1 条候选证据 | warning |
| 8 | 弱依据检查 | 标记 direct 的选项至少引用 1 张句卡 | warning |
| 9 | 答案对照提示 | detected_answer 与 AI 预测答案一致 | warning（不一致时提示教研复核） |

## 判定规则

- 任一 fail → `needs_review`
- 任一 warning → `needs_review`
- 全部 pass → `passed`
