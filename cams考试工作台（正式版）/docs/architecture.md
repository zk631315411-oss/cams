# V2 架构边界

## 运行关系

```text
教研网页 -> backend/api.py ----\
                               -> backend/storage.py -> data/questions / audit / releases
Codex GUI -> backend/mcp_server.py /
                    |
                    -> backend/retrieval -> data/infrastructure + runtime/models/bge-m3
```

网页和 MCP 是两个入口，不是两套业务系统。涉及题目档案的正式写入都必须经过 `WorkspaceStore`；业务模块不得直接覆盖题目 JSON 或 JSONL。

## 业务模块

- `frontend`：只调用 HTTP API。负责阅读、证据确认、解析批注和教研决定，不负责自动运行 Codex。
- `backend/api.py`：网页、教材阅读器和教研动作的 HTTP 边界；仍保留部分旧流程兼容端点。
- `backend/mcp_server.py`：Codex stdio MCP 边界，提供研究、登记、解析、核验和发布工具。
- `backend/storage.py`：唯一正式写入层，包含原子写入、锁、乐观版本、审计、V2 工作流和发布门禁。
- `backend/retrieval`：一般检索与题目检索；读取冻结教材、索引、KG、术语和本地 BGE-M3。
- `backend/drafting/deepseek.py`：可选 DeepSeek 第二意见，不推进正式流程。
- `backend/drafting/service.py`：旧 DS 草稿输入兼容链路，待确认无调用者后删除。
- `backend/infrastructure/catalog.py`：当前无调用者的读取骨架，由接手开发者决定去留。
- `backend/review`：预留模块边界；当前没有实现，审核和发布规则仍在 `storage.py`。

## 数据边界

- `data/infrastructure`：冻结教材、向量索引、KG 和 P5 术语。日常处理只读。
- `data/questions/<question_id>`：单题完整档案。V2 阶段以 `workflow.json` 为准。
- `data/control`：当前题、题目锁、题号锁和发布锁等临时控制状态。
- `runtime/models/bge-m3`：模型资产。模型文件存在不能证明 Python 依赖兼容。
- `releases/<release_id>`：只由发布构建器生成的不可变快照。

## 正式流程与任务状态

正式阶段：

```text
intake -> duplicate_check -> evidence_research -> evidence_confirmation
       -> analysis_drafting -> analysis_revision -> final_verification
       -> human_approval -> release_ready -> released
```

`task_state.json` 只描述当前执行者、任务运行状态、等待对象和下一步。任务完成不等于正式阶段通过，后台任务也不得自动换题、切标签或跳转 PDF。

## 一致性规则

1. 同一题一次只能有一个写操作，不同题可以并行。
2. 题面内容变化才递增 `question.version`；任何正式档案写入递增 `archive_revision`。
3. 写入方提交 `expected_question_version` 和 `expected_archive_revision`，陈旧写入必须失败。
4. 证据、解析、核验和批准均绑定具体版本，历史只能失效，不能删除或覆盖。
5. 发布只接受题面、证据确认、解析、最终核验和人工批准版本完全一致的题目。
6. DeepSeek 成功、失败或未配置均不得改变正式阶段。

详细状态和文件契约分别见 [workflow-v2.md](workflow-v2.md) 与 [data-schema.md](data-schema.md)。
