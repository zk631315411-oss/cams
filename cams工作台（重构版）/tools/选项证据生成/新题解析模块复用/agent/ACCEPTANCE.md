# Agentic Retrieval 验收标准

本文件定义 agentic retrieval 层进入主流程前必须满足的验收标准。

## 1. 流程正确性

- Stage 0 必须只接收题干和选项，不能接收标准答案、教研解析、历史解析。
- Stage 1 必须基于 Stage 0 的待验证命题生成检索任务，不能只复述题干。
- Stage 2 的最终候选必须来自真实教材句卡。
- Stage 3 必须逐选项判断证据覆盖情况。
- Stage 4 补搜必须由 Stage 3 的缺口触发，不能无限扩散。
- Stage 5 最终裁判不能看到标准答案和教研解析。

## 2. 泄露检查

任一 LLM prompt 中不得出现以下内容：

- `标准答案`
- `正确答案`
- `教研解析`
- `参考答案`
- 题库答案字段
- 已知答案对照结果

允许在后验质检阶段使用标准答案，但后验质检输出不能回流给 blind adjudicator/reviewer。

## 3. 检索质量

对同一批测试题，agentic retrieval 至少应满足：

- 不低于当前整题直接检索的正确证据覆盖率。
- 对多选题，能分别覆盖多个正确选项的核心依据。
- 对错误选项，能提供可用于排除的 direct 或 partial evidence。
- 对直接检索漏掉的关键教材句卡，至少在部分样例中能通过补搜召回。

## 4. 输出可审计

每道题必须保存完整 debug JSON，包括：

- Stage 0 初判结果
- Stage 1 search tasks
- 每个 search task 的候选句卡
- Stage 3 evidence gap audit
- followup tasks
- 最终候选证据池

每条最终候选证据必须能追溯到：

- 由哪个 search task 召回
- 通过哪些检索源命中
- 原始 `card_id`
- 原始教材句卡 `citation`

## 5. 成本与耗时

默认配置下：

- Stage 0 调用 1 次 LLM。
- Stage 1 调用 1 次 LLM。
- Stage 3 调用 1 次 LLM。
- followup 最多 1 轮。
- 单题总 LLM 调用默认不超过 4 次。
- 单题检索任务数量默认不超过 12 个。
- 单题候选句卡进入最终裁判前默认不超过 40 条。

如果超过上限，必须降级为 `needs_teacher_review`，不能无限等待。

## 6. 可回退

主流程接入时必须保留开关：

```text
--agentic-retrieval
--no-agentic-retrieval
```

默认是否开启由测试结果决定。

当 agentic retrieval 任一阶段失败时，应回退到当前整题直接检索流程，并在结果中记录：

```json
{
  "agentic_retrieval": {
    "enabled": true,
    "status": "fallback",
    "reason": "失败原因"
  }
}
```

## 7. 人工验收样例

第一批人工验收至少包含：

- 2 道单选题。
- 2 道多选题。
- 1 道直接检索曾经漏关键证据的题。
- 1 道题目表述和教材术语不一致的题。
- 1 道需要错误项反证的题。

每题需要对比：

- 当前整题直接检索召回了什么。
- agentic retrieval 新增召回了什么。
- 新增证据是否真的有用。
- 是否引入噪声。
- 最终答案是否更稳定。

## 8. 不通过条件

出现以下任一情况，不得接入主流程：

- prompt 泄露标准答案或教研解析。
- Stage 0 初判答案被直接传给最终裁判，导致答案锚定。
- 候选证据大量偏离教材原文。
- 补搜引入明显无关证据，且没有被 Stage 3 识别。
- 多选题仍只覆盖一个正确选项。
- 单题耗时或 LLM 调用次数明显不可控。
