# 后端

`backend` 提供网页 HTTP API、Codex MCP、唯一文件存储层、教材阅读、检索、可选 DeepSeek、备份和迁移工具。它不是标准化安装的 Python 包；当前入口通过脚本或直接执行文件运行，并使用脚本式顶层导入。

## 入口与文件

| 文件/目录 | 当前职责 |
| --- | --- |
| `api.py` | 静态前端与 HTTP API；启动时尝试每日备份 |
| `mcp_server.py` | stdio MCP `2.1.0`，19 个工具 |
| `storage.py` | 唯一正式写入层、锁、审计、V2 工作流和发布构建 |
| `textbook.py` | 双语 PDF 信息、页面渲染和原文坐标匹配 |
| `backup.py` | 备份可变题库、控制状态和发布包；当前没有恢复实现 |
| `migrate_workflow_v2.py` | 旧档案到 V2 的预览和迁移 |
| `import_legacy.py` | 一次性导入旧题面及旧 DS 原件 |
| `retrieval/` | 一般检索和题目检索 |
| `drafting/` | 可选 DeepSeek 与旧 DS 兼容链路 |
| `infrastructure/` | 当前未使用的基础设施读取骨架 |
| `review/` | 预留模块边界，当前无实现 |

接口和数据细节见 [HTTP API](../docs/api.md)、[MCP 工具](../docs/mcp-tools.md)、[数据结构](../docs/data-schema.md) 与 [V2 工作流](../docs/workflow-v2.md)。

## 写入边界

- API、MCP 和业务服务不得绕过 `WorkspaceStore` 直接修改题目档案。
- JSON 通过临时文件和 `os.replace` 原子替换；JSONL 只追加。
- 同题写入由 `data/control/locks/<question_id>.json` 排他锁保护；发布另有全局锁。
- 写入必须提交当前 `question.version` 和 `archive_revision`，陈旧版本会被拒绝。
- `data/infrastructure` 在日常运行中只读。

## 当前 V2 与旧兼容

V2 使用证据候选、证据确认、正式解析、最终核验和工作流决定。以下仍在代码中，但属于 Deprecated 兼容能力：

- API：`ds-draft`、`codex-review`、`decision`、`evidence-review`、`draft-input`。
- 存储：`write_ds_draft`、`write_codex_review`、旧 `record_decision`、旧发布回退分支。
- `drafting/service.py`：旧 DS 草稿输入准备。

这些能力待接手开发者确认没有外部调用者后删除。在删除前，文档必须如实列出，但新功能不得调用或扩展它们。

## 运行

```powershell
.\scripts\start-web.ps1 -Port 8765
.\scripts\start-mcp.ps1
```

直接调试时应从工作台根目录运行，并显式传入 `--workspace-root`。检索还需要可用的 BGE-M3 运行环境；当前依赖组合存在已知加载故障。

## 配置

- `--workspace-root`：API/MCP/迁移脚本的工作台根目录参数。
- `CAMS_WORKSPACE_ROOT`：部分路径解析的环境变量；入口脚本会设置。
- `CAMS_BGE_MODEL_PATH`：本地 BGE-M3 模型目录。
- `settings.toml`：当前只有 `[retrieval]` 被读取；示例中的其他配置段尚未接入代码。
- DeepSeek API Key：保存在用户本机私密配置目录，不进入项目、审计或备份。

## 测试与限制

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

现有 27 项测试不覆盖真实 BGE、HTTP 路由、MCP 进程协议、恢复或 macOS。详见 [tests/README.md](../tests/README.md) 和 [已知问题](../docs/已知问题与后续任务.md)。
