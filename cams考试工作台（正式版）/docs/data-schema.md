# 题目数据结构

每道题位于 `data/questions/<question_id>/`。本文是字段级维护说明，不是机器可验证 JSON Schema；当前代码仍允许题面 `content` 保留历史扩展字段。

## 核心版本

| 字段 | 位置 | 语义 |
| --- | --- | --- |
| `question.version` | `question.json` | 题面内容版本；只有内容变化时递增 |
| `archive_revision` | `question.json` | 任何正式档案写入后的乐观并发修订号 |
| 各记录 `version` | 对应 JSON/JSONL | 该类证据、解析、核验或决定的独立版本 |
| `workflow.references` | `workflow.json` | 当前正式阶段绑定的目录、候选、确认、解析、核验和决定版本 |

写入方不能用某一种版本代替另一种版本。

## 核心文件

### `question.json`

```json
{
  "question_id": "v7_q_000001",
  "version": 1,
  "archive_revision": 5,
  "status": "ready_for_ds",
  "content": {},
  "updated_at": "UTC ISO-8601"
}
```

`status` 是旧兼容状态；V2 阶段读取 `workflow.json`。`content` 常含 `stem`、`options`、`answer`、题型、中英文题面和来源扩展字段。

### `workflow.json`

字段：`schema_version=cams-workflow/v2`、题号、`stage`、`disposition`、`question_version`、`duplicate_check`、`references`、更新时间，以及迁移题的 `legacy_status`/`migration_status`。

### 任务文件

- `task_state.json`：当前 `task_type`、`status`、`actor`、`waiting_for`、`next_step`、`error`、`summary` 和时间。
- `task_history.jsonl`：每次任务状态快照，只追加。

任务文件不决定正式阶段。

## 题源与准入

- `source/files/`：归档后的 PNG/JPG/JPEG/PDF。
- `source/intake.json`：来源类型、说明、原始编号/链接、接收时间、答案状态、原始文本、附件哈希、缺失字段和复制错误。
- `duplicate_check.json`：题面版本、候选、判断、理由、操作者和时间。当前 merge 只含自由文本，不含目标题号。

迁移题还可能有 `source/legacy_question.json` 和 `source/legacy_ds_result.json`。

## 证据文件

- `retrieval_runs.jsonl`：`cams-retrieval-run/v2`；保存轮次、查询、参数、资产版本、证据 ID 和原始结果。
- `evidence_catalog.json`：`cams-evidence-catalog/v2`；跨轮去重后的证据，包含原文、页码、来源、发现历史、Codex 精选和教研建议。
- `evidence_candidates.jsonl`：`cams-evidence-candidate/v2`；Codex 提交的候选版本及证据作用。
- `evidence_confirmation.json`：`cams-evidence-confirmation/v2`；教研当前确认或退回记录。
- `evidence_confirmation_history.jsonl`：被替换、退回或重开的旧确认，只追加。

教材证据以教材版本和 `unit_id` 优先去重；无 unit_id 时使用页码和规范化原文；外部资料使用规范 URL 和引文。

## 解析、核验和决定

- `analysis_versions.jsonl`：`cams-analysis/v2`；绑定题面版本和证据确认版本，正文含固定五板块。
- `analysis_feedback.jsonl`：教研批注，含 `feedback_id`、解析版本、板块和评论。
- `final_checks.jsonl`：`cams-final-check/v2`；绑定题面、证据确认和解析版本。
- `decision.json`：V2 为 `cams-decision/v2`，绑定题面、证据确认、解析、最终核验和决定版本。
- `ds_opinions.jsonl`：可选第二意见，包含输入快照、模型、结构化结果或错误，不推进正式阶段。

## 审计

`audit.jsonl` 每行包含：

- `at`、`actor`、`channel`、`operation`、`reason`
- `before_hash`、`after_hash`

审计只保存结构化内容哈希，不保存完整前后副本。因此“可追溯操作”不等同于“能从审计恢复任意历史内容”；完整历史依赖版本化 JSONL、history 文件和备份。

## Deprecated 文件

迁移题或旧流程可能存在 `evidence_review.json`、`ds_draft.json`、`codex_review.json` 和旧 schema 的 `decision.json`。这些文件必须保留供追溯，但不得成为有 `workflow.json` 的 V2 题目发布依据。

## 控制与发布

- `data/control/active-context.json`：临时网页选择，不递增题目版本或审计。
- `data/control/locks/*.json`：同题排他锁。
- `data/control/question-id-lock.json`：题号分配锁。
- `data/control/release-lock.json`：发布构建锁。
- `releases/<release_id>`：结构见 [releases/README.md](../releases/README.md)。
