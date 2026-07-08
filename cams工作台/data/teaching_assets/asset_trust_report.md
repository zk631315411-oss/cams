# Teaching Assets 可信度审查报告

生成日期：2026-06-24
审查范围：`cams工作台/data/teaching_assets`

## 总览

- 教材阅读区卡片 ID：2124
- 全书句卡：5197
- 题目：179
- 已有选项级证据题目：179
- 统一候选考点：760
- 原文-考点映射行：1580
- 答疑绑定：37（本轮仅作辅助线索）
- KG 节点/章节：1853 / 99（本轮仅作概念辅助）

## 可信度分布

### 选项 -> 教材证据

- `trusted`：0
- `high_candidate`：286
- `medium_candidate`：325
- `low_candidate`：0
- `invalid_or_blocked`：139

### 考点候选

- `trusted`：0
- `high_candidate`：138
- `medium_candidate`：544
- `low_candidate`：71
- `invalid_or_blocked`：7

## 关键风险

- 题库内部冲突：0 条。题干/选项/答案原则上可信，但互相冲突时必须标红，不能自动修。
- 未映射到当前第二章阅读区的考点：54 条。可能是跨章节证据或 quote 无法回贴。
- QA 绑定未人工确认：37 条。本轮不能直接作为正式错因来源。

## 样例：不可直接使用的关系

- 选项证据 `2.1_18 A`：no_usable_direct_evidence
- 选项证据 `2.1_18 D`：no_usable_direct_evidence
- 选项证据 `2.1_19 C`：no_usable_direct_evidence
- 选项证据 `2.1_19 D`：no_usable_direct_evidence
- 选项证据 `2.1_2 A`：no_usable_direct_evidence
- 选项证据 `2.1_21 A`：no_usable_direct_evidence
- 选项证据 `2.1_21 D`：no_usable_direct_evidence
- 选项证据 `2.1_22 C`：no_usable_direct_evidence
- 选项证据 `2.1_24 A`：no_usable_direct_evidence
- 选项证据 `2.1_25 A`：no_usable_direct_evidence

## 样例：低可信候选

- 考点 `ep_opt_v6s_n00037`：no_direct_option_evidence, status_requires_manual_review
- 考点 `ep_opt_v6s_n00071`：no_direct_option_evidence, status_requires_manual_review
- 考点 `ep_opt_v6s_n00318`：no_direct_option_evidence, status_requires_manual_review
- 考点 `ep_opt_v6s_n00346`：mixed_option_evidence, status_requires_manual_review
- 考点 `ep_opt_v6s_n00410`：no_direct_option_evidence, status_requires_manual_review
- 考点 `ep_opt_v6s_n00749`：no_direct_option_evidence, status_requires_manual_review
- 考点 `ep_opt_v6s_n00845`：cannot_backproject_to_current_reader
- 考点 `ep_opt_v6s_n00856`：no_direct_option_evidence, status_requires_manual_review
- 考点 `ep_opt_v6s_n00858`：cannot_backproject_to_current_reader
- 考点 `ep_opt_v6s_n01028`：mixed_option_evidence, status_requires_manual_review

## 下一步建议

- HTML 默认显示全部候选，但必须按可信度显示标识和筛选。
- `trusted` 只从未来的 `teaching_review_decisions.json` 读取，不由脚本自动生成。
- 先处理 `invalid_or_blocked`：题目数据冲突、正确选项无 direct 证据、无法回贴原文。
- QA/KG 继续作为辅助面板，不参与正式考点确认。
