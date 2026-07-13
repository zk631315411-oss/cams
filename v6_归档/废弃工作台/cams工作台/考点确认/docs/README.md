# 考点确认工作区

这个目录用于在现有证据绑定基础上，生成更适合老师界面展示的参考考点数据。

当前原则：

- 不重新检索证据卡，优先使用 `data/teaching_assets/option_evidence_map.json` 中已有的题目、选项、证据卡绑定。
- 不覆盖现有工作台数据，所有中间产物写入本目录下的 `outputs/`、`cache/`、`reports/`。
- 第一阶段先做证据信号整理和规则打分，后续再接入 LLM 做受限判断、合并和命名。

目录说明：

- `scripts/`：离线生成脚本。
- `outputs/`：结构化输出，供后续脚本或前端试验读取。
- `reports/`：便于人工快速查看的报告。
- `prompts/`：后续 LLM 判断使用的提示词模板。
- `cache/`：后续 LLM 调用缓存。
- `docs/`：工作说明和设计记录。

当前第一步输出：

- `outputs/evidence_signals.jsonl`：每一行是一条“题目选项 -> 证据卡”的明细信号。
- `outputs/evidence_card_scores.json`：按证据卡聚合后的候选分数和角色提示。
- `outputs/evidence_signal_summary.json`：统计摘要。
- `reports/evidence_signal_sample.md`：便于快速扫一眼的样例报告。
