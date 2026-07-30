# 数据目录

`data` 保存冻结基础设施、题目长期档案和临时控制状态。正式题目不得由编辑器或脚本直接覆盖，应通过 `WorkspaceStore`、HTTP API 或 MCP 操作。

## 目录

- `infrastructure/textbook`：双语教材 PDF、教材单元、章节、页码映射和 manifest。
- `infrastructure/index`：冻结向量/BM25 索引、单元映射和 manifest。
- `infrastructure/kg`：检索图谱和 manifest。
- `infrastructure/terms`：P5 术语别名索引和 manifest。
- `questions/<question_id>`：单题完整档案。
- `control/active-context.json`：网页当前题，不进入正式版本或审计。
- `control/locks`、`question-id-lock.json`、`release-lock.json`：运行时排他锁，按需产生并在正常结束后删除。

## 单题档案

V2 常用文件见 [数据结构契约](../docs/data-schema.md)。文件按流程逐步生成，缺少尚未到达阶段的文件是正常现象。

`workflow.json` 是正式阶段权威；`question.json.status` 是旧兼容字段。迁移题还可能包含 `evidence_review.json`、`ds_draft.json`、`codex_review.json` 或旧 `decision.json`，不得把这些文件重新用作 V2 发布依据。

## 写入规则

- JSON 使用原子替换；JSONL 只追加。
- `question.version` 只在题面内容变化时递增。
- `archive_revision` 在题目档案写入时递增。
- `audit.jsonl` 只记录时间、操作者、入口、操作、理由及前后内容哈希，不保存完整前后副本。
- 不手工删除题目目录。当前题号算法扫描现存最大编号，删除最大编号会导致编号可能复用。
- 冻结基础设施更新必须同步 manifest、版本和 SHA-256，并重启使用进程以清除缓存。

## 备份

每日备份只包含 `questions`、`control` 和 `releases`，不重复复制冻结基础设施或模型。当前有备份生成器但没有恢复工具；任何恢复操作都应在接手者实现并验收后进行。
