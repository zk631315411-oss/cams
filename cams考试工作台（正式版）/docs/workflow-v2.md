# V2 工作流契约

V2 将正式里程碑、处置状态和运行任务分开。`workflow.json` 是正式阶段权威；`task_state.json` 不是审批记录；`question.status` 只用于旧兼容。

## 正式阶段

| 阶段 | 含义 | 正常下一步 |
| --- | --- | --- |
| `intake` | 题源或题面尚未通过准入 | 补齐后进入重复检查；当前缺少补全接口 |
| `duplicate_check` | 等待 Codex 判重或教研判断 | 新题进入证据研究；合并题停止 |
| `evidence_research` | 登记、去重和精选证据 | Codex 提交证据候选 |
| `evidence_confirmation` | 等待教研确认或退回 | 确认后生成解析，退回后补证 |
| `analysis_drafting` | 等待第一版正式解析 | Codex 写入版本 |
| `analysis_revision` | 教研批注与 Codex 修订 | 教研标记润色完成 |
| `final_verification` | Codex 核对固定题面、证据和解析 | 通过后等待教研决定 |
| `human_approval` | 教研批准、退回、暂缓或不收录 | 批准后可发布 |
| `release_ready` | 当前绑定版本满足发布条件 | 构建发布包 |
| `released` | 已包含在某个发布包 | 终态记录 |

## 处置状态

- `active`：正常推进。
- `needs_source_clarification`：题源或题面不完整。
- `merged`：已合并为既有题，不再推进。
- `held`：教研暂缓。
- `rejected`：不收录但保留档案。

处置状态和阶段必须一起判断。例如 `human_approval / held` 不是可发布状态。

## 任务状态

任务状态为 `idle|running|waiting|completed|failed`。它记录执行者、等待对象和下一步，但不得自动推进正式里程碑。

DeepSeek 使用 `task_type=ds_opinion`，无论完成或失败都返回原正式流程。

## 主要转移

```text
create_question_intake
  完整 -> duplicate_check / active
  不完整 -> intake / needs_source_clarification

resolve_duplicate_check
  new -> evidence_research / active
  merge -> duplicate_check / merged
  hold -> duplicate_check / active

submit_evidence_candidate -> evidence_confirmation
evidence confirm -> analysis_drafting
evidence return -> evidence_research
write_analysis_version -> analysis_revision
polishing complete -> final_verification

final check
  passed -> human_approval
  needs_analysis -> analysis_revision
  needs_evidence -> evidence_research
  needs_question -> duplicate_check

human decision
  approved -> release_ready / active
  returned -> analysis_revision / active
  hold -> human_approval / held
  rejected -> human_approval / rejected

build_release -> released / active
```

## 证据重开与失效

`reopen_evidence` 或最终核验 `needs_evidence` 会：

- 将当前证据确认写入历史并标记 reopened。
- 返回 `evidence_research`。
- 清除 workflow 中当前确认、解析、最终核验和决定引用。
- 保留所有旧候选、解析、核验、决定和审计文件。

题面内容修改也会按存储规则使下游版本失效。历史记录不能物理删除来“清理状态”。

## 发布门禁

V2 发布要求：

1. `stage=release_ready` 且 `disposition=active`。
2. `decision.json` 为 `cams-decision/v2` 且 `decision=approved`。
3. 当前证据确认状态为 confirmed。
4. 最新正式解析存在。
5. 最新最终核验为 passed。
6. 决定绑定的题面、证据、解析和核验版本与当前文件完全一致。

任一版本变化后，旧批准不得发布。

## 旧状态映射

`question.status` 可能仍出现 `ready_for_ds`、`ds_draft`、`approved` 等值。读取旧档案时存储层会映射到 V2，但已有 `workflow.json` 后必须以 V2 为准。新代码不得根据旧状态推进正式流程。
