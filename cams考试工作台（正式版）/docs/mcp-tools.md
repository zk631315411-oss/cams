# Codex MCP 工具契约

实现：`backend/mcp_server.py`。服务名 `cams-formal-workbench`，版本 `2.1.0`，stdio JSON-RPC，当前有 19 个工具。

MCP 顶层 schema 只把复杂参数声明为 `object` 或 `object_array`；下文记录当前存储层实际要求。调用前仍应读取代码和最新题目状态。

## 通用规则

- 除新题建档外，正式写入前先调用 `read_question`。
- 写入提交 `expected_question_version` 与 `expected_archive_revision`；`resolve_duplicate_check` 当前只要求修订号。
- `reason` 记录到审计或业务记录，不应填写空泛文本。
- `actor` 缺省为 `codex`。
- `update_question`、`request_ds_opinion`、`build_release` 被标记为破坏性，并要求 `confirmed=true`。
- MCP 不提供教研证据确认、解析批注、润色完成或正式批准工具；这些动作只能通过网页 API。

## 读取与检索

| 工具 | 参数 | 返回/说明 |
| --- | --- | --- |
| `list_questions` | 可选 `status`、`query`、`offset`、`limit` | 题号、版本、修订号、旧状态、V2 阶段、处置状态和题干 |
| `read_active_context` | 无 | 浏览器当前题和建议动作；收到“整理证据”“处理当前题”时先调用 |
| `read_question` | `question_id` | 题面、流程、任务、intake、判重、精选摘要、候选、确认、解析、批注、核验和决定 |
| `read_evidence_catalog` | `question_id`；可选 `scope`、`source_kind`、`method`、`option`、`run_id`、`offset`、`limit` | 分页证据目录；scope 为 `all|curated|suggested` |
| `read_audit` | `question_id` | 追加式题目审计 |
| `search_evidence` | `query`；可选 `top_k`、`language`、`config` | 一般 RAG+KG 结果，不包含题目检索头和 P5 |
| `retrieve_question_evidence` | `question_id`；可选 `config` | 题目检索、P5、选项补充和 KG 结果；只读，不自动登记 |

## 新题与重复检查

### `create_question_intake`

必填：`content`、`intake`、`source_paths`、`reason`。

- `content`：至少 `stem`/`stem_cn` 和非空 `options`；答案可空。
- `intake`：可含 `source_type`、`source_description`、`original_source_id`、`original_link`、`answer_status`、`raw_text`。
- `source_paths`：本机可访问的 PNG/JPG/JPEG/PDF；每个不超过 20 MB。

返回新题、V2 workflow、intake 和重复候选。附件或题面不完整时进入待补题源，但当前没有后续补全工具。

### `resolve_duplicate_check`

必填：`question_id`、`decision`、`rationale`、`reason`、`expected_archive_revision`。

`decision` 支持 `new|merge|hold` 及对应中文值。`new` 进入 `evidence_research`；`merge` 处置为 `merged`；`hold` 保持待判断。当前 `merge` 没有结构化目标题号字段。

## 证据研究

### `register_evidence`

必填：题号、`payload`、`discovery_method`、理由和两个预期版本。

发现方式只能是：`question_rag`、`general_rag`、`kg_expand`、`grep_keyword`、`direct_page_review`、`external_search`、`legacy_import`。

`payload` 可包含 `items`、`main_candidates`、`kg_candidates` 和按选项分组的 `option_supplements`。教材证据优先提供 `unit_id`、原文和页码；外部资料提供规范 URL、引文、机构和标题。登记会生成检索轮次、去重证据目录和审计。

### `curate_evidence`

`updates[]` 包含 `evidence_id`、`selected`、`role`、可选 `target_option`/`note`。选中项的 `role` 必须为：

- `support_answer`
- `exclude_option`，且必须给 `target_option`
- `background`

### `submit_evidence_candidate`

要求当前为 `evidence_research` 且至少一条 Codex 精选证据。提交后进入 `evidence_confirmation`，等待教研网页确认或退回。

### `reopen_evidence`

要求已有 confirmed 证据和非空理由。将证据确认标记为 reopened，清空后续版本引用并返回 `evidence_research`，历史记录保留。

## 正式解析与核验

### `write_analysis_version`

`analysis` 必须包含：

- `exam_point`
- `core_analysis`
- `option_analysis`，对象或数组
- `pitfall`
- `evidence`，数组

只允许在 `analysis_drafting|analysis_revision` 且存在 confirmed 证据时调用。若有教研批注，`feedback_responses[]` 必须引用有效 `feedback_id`，状态为 `addressed|not_addressed` 并填写回应。

### `write_final_check`

`check.status` 为 `passed|needs_analysis|needs_evidence|needs_question`，`check.checks` 必须是数组，可附 `summary`。

- `passed` -> `human_approval`
- `needs_analysis` -> `analysis_revision`
- `needs_evidence` -> `evidence_research` 并重开证据
- `needs_question` -> `duplicate_check`

### `set_task_state`

记录运行任务，不推进正式阶段。`status` 为 `idle|running|waiting|completed|failed`，可提供 `waiting_for`、`next_step`、`error`、`summary`。

## 可选研判、改题和发布

- `request_ds_opinion`：要求 `confirmed=true`；输入去除答案字段并使用精选证据快照，结果不改变正式阶段。
- `update_question`：要求 `content`、两个预期版本、理由和 `confirmed=true`；内容变化使下游版本失效。
- `build_release`：要求 `release_id`、理由和 `confirmed=true`；发布 ID 必须以 `v7-` 开头且不能覆盖同名目录。

返回结构以 `structuredContent` 和同内容的文本 JSON 同时提供。错误以 MCP error 响应返回，当前没有稳定错误代码枚举。
