# HTTP API 契约

实现入口：`backend/api.py`。服务只绑定本机时没有用户认证机制，不应直接暴露到局域网或公网。响应除教材 PNG 外均为 JSON。

## 通用写入字段

题目档案写入通常要求：

| 字段 | 说明 |
| --- | --- |
| `actor` | 操作者；缺省为 `educator` |
| `reason` | 操作理由；多数正式写入不能为空 |
| `expected_question_version` | 读取时看到的题面版本 |
| `expected_archive_revision` | 读取时看到的档案修订号 |
| `confirmed` | 修改题目、确认/退回、润色完成、人工决定和发布等关键动作必须为 `true` |

锁冲突返回 409；无效写入、版本冲突、资产错误和 JSON 错误通常返回 400；不存在的 GET 资源返回 404。当前代码未使用统一错误枚举，错误正文为 `{"ok": false, "error": "..."}`。

## GET

| 路由 | 参数 | 返回 |
| --- | --- | --- |
| `/api/health` | 无 | `{"ok": true}`；当前不包含应用身份或依赖健康度 |
| `/api/active-context` | 无 | 网页当前题、V2 阶段、处置状态和建议动作 |
| `/api/settings/deepseek` | 无 | 脱敏的启用状态、地址、模型和 `configured` |
| `/api/textbook/manifest` | 无 | 教材版本、页数和资源信息 |
| `/api/textbook/chapters` | 无 | 教材章节 JSON |
| `/api/textbook/page` | `lang=zh|en`、`page`、`scale` | 渲染后的 `image/png` |
| `/api/questions` | `status`、`query`、`offset`、`limit`；limit 1-500 | 题目摘要分页结果 |
| `/api/questions/<qid>` | 无 | `workflow_detail`：题面、流程、任务、证据、解析、核验和决定摘要 |
| `/api/questions/<qid>/audit` | 无 | 追加式审计数组 |
| `/api/questions/<qid>/tasks` | 无 | 任务历史数组 |
| `/api/questions/<qid>/evidence` | `scope`、`source_kind`、`method`、`option`、`run_id`、`offset`、`limit` | 证据目录分页结果，limit 最大 100 |
| `/api/questions/<qid>/source/<filename>` | 文件名必须出现在 intake 附件清单 | 题源原件，inline 返回 |
| `/api/releases` | 无 | 发布 manifest 列表 |
| `/api/releases/<release_id>/manifest` | 无 | 指定发布 manifest |

## POST：设置和教材

| 路由 | 请求 | 行为 |
| --- | --- | --- |
| `/api/settings/deepseek` | `enabled`、`base_url`、`model`、可选 `api_key` | 写入用户本机私密配置，不进入项目 |
| `/api/active-context` | `question_id` | 更新网页当前题，不改变题目版本、修订号或审计 |
| `/api/textbook/match` | `language`、`page`、`query` | 返回匹配方式和归一化文字框 |
| `/api/questions` | 任意 | 固定返回 405；新题只能由 MCP 建档 |
| `/api/releases` | `release_id`、`actor`、`reason`、`confirmed=true` | 构建不可变发布包，成功返回 201 |

## POST：V2 教研动作

以下路由均为 `/api/questions/<qid>/<action>`，并要求通用版本字段。

| action | 额外字段 | 当前门禁 |
| --- | --- | --- |
| `evidence-suggestion` | `updates[]`：`evidence_id`、`selected`、`role`、可选 `target_option`/`note` | 仅 `evidence_research`；教研建议不会直接成为 Codex 正式候选 |
| `evidence-decision` | `action=confirm|return`、`confirmed=true` | 仅 `evidence_confirmation`；退回必须有理由 |
| `analysis-feedback` | `section`、`comment` | 仅 `analysis_revision`，批注不能为空 |
| `polishing-complete` | `confirmed=true` | 所有批注必须已在最新解析版本中回应 |
| `workflow-decision` | `decision=approved|returned|hold|rejected`、`confirmed=true` | 仅 `human_approval`；非批准决定必须有理由 |

网页不提供 Codex 证据登记、候选提交、解析写入和最终核验端点；这些动作由 MCP 完成。

## POST：检索与 Deprecated 兼容

| action | 状态 | 说明 |
| --- | --- | --- |
| `search` | 当前存在 | 一般检索；请求 `query`、`top_k`、`language`、`config` |
| `retrieve` | 当前存在 | 当前题目检索；使用题面 `content` |
| `ds-draft` | Deprecated | 写旧 DS 草稿 |
| `codex-review` | Deprecated | 写旧 Codex 核验 |
| `decision` | Deprecated | 写旧人工决定 |
| `evidence-review` | Deprecated | 写旧证据采用/排除记录 |
| `draft-input` | Deprecated | 准备旧 DS 草稿输入 |

旧接口待确认没有外部调用者后删除。新前端和新集成不得继续使用。

## PUT

`PUT /api/questions/<qid>` 修改题面：

```json
{
  "content": {},
  "actor": "educator",
  "reason": "修改原因",
  "expected_question_version": 1,
  "expected_archive_revision": 5,
  "confirmed": true
}
```

内容变化会递增 `question.version`，使旧证据确认、解析、最终核验和批准失效，并按当前代码重置到需要重新检查的阶段。
