# CAMS 正式工作台

CAMS 正式工作台将新题、教材证据、正式解析、教研决定和发布版本保存在同一套可追溯档案中。当前目录是供开发者继续完善的 Windows 开发候选版，不是已经通过 M3 iMac 验收的成品包。

本目录是 CAMS 交接仓库中的可维护副本。为避免把平台绑定环境逐文件混入源码，仓库副本不包含 `.venv` 和 `runtime`；包含这些文件、原独立 Git 基线 `d93697374eab7ad5d23813c9ca5ae708eaf7192f` 及全部本机状态的完整快照见 [`../项目交接/正式工作台完整快照/`](../项目交接/正式工作台完整快照/README.md)。

## 当前基线

- 正式流程：`接收整理 -> 重复检查 -> 证据研究 -> 证据确认 -> 正式解析 -> 最终核验 -> 教研批准 -> 发布`。
- 题库：395 道迁移题，当前均处于 V2 `evidence_research / active`。
- 测试：当前 Windows 环境有 27 项单元测试通过。
- MCP：`cams-formal-workbench 2.1.0`，当前暴露 19 个工具。
- 发布：`releases/` 当前为空。
- 已知阻塞：现有依赖组合无法真实加载 BGE-M3；检索 CLI、恢复流程和 macOS arm64 正式包尚未完成。

以上状态以代码、测试和实际文件为准。开始开发前先阅读 [开发交接说明](docs/开发交接说明.md) 和 [已知问题与后续任务](docs/已知问题与后续任务.md)。

## 快速开始

从完整快照复原或当前机器已有 `.venv` 时：

```powershell
cd "<workbench-root>"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\scripts\start-web.ps1 -Port 8765
```

浏览器地址：`http://127.0.0.1:8765`。

全新 Windows 环境可运行 `scripts/setup.ps1`，但依赖尚未锁定，当前 BGE-M3 真实加载也存在已知故障；安装脚本结束不能替代真实 `encode` 和检索验收。详见 [scripts/README.md](scripts/README.md) 与 [runtime/README.md](runtime/README.md)。

Codex 使用 stdio MCP：

```text
command: powershell.exe
args: ["-ExecutionPolicy", "Bypass", "-File", "<workbench-root>\scripts\start-mcp.ps1"]
```

当前正式版根目录不包含可直接移植的 `.codex/config.toml`。接手机器需要按自己的绝对路径生成项目级配置，不能照搬当前开发机配置。

## 目录

| 目录 | 职责 | 入口说明 |
| --- | --- | --- |
| `frontend/` | 题目/PDF 分屏、证据确认、解析批注和教研决定 | [frontend/README.md](frontend/README.md) |
| `backend/` | HTTP API、MCP、存储、教材、检索、备份和迁移 | [backend/README.md](backend/README.md) |
| `data/` | 冻结基础设施、题目长期档案和临时控制状态 | [data/README.md](data/README.md) |
| `runtime/` | 本地 BGE-M3 等运行资源 | [runtime/README.md](runtime/README.md) |
| `scripts/` | Windows、portable 和 macOS 的安装、启动与构建脚本 | [scripts/README.md](scripts/README.md) |
| `tests/` | 文件规则、工作流和教材服务单元测试 | [tests/README.md](tests/README.md) |
| `releases/` | 不可变发布快照 | [releases/README.md](releases/README.md) |
| `docs/` | 架构、契约、交接状态和配置示例 | [docs/README.md](docs/README.md) |

## 不可破坏的边界

- 网页只通过 HTTP API 操作；Codex 只通过 MCP 操作；正式题目写入最终都经过 `backend/storage.py`。
- `data/infrastructure` 是冻结资产。日常网页、MCP 和题目处理不得修改它。
- `workflow.json` 是 V2 正式阶段权威记录；`question.json.status` 仍包含旧兼容状态，不得用它覆盖 V2 阶段。
- 题面内容变化递增 `version`；任何档案写入递增 `archive_revision`。写入方必须提交读取时看到的版本。
- 修改题面、证据或解析后，旧的证据确认、最终核验和批准不得继续用于发布。
- DeepSeek 只提供可选第二意见，不是正式流程阶段。旧 DS 草稿接口仍存在于代码中，但已进入待确认调用者后删除的兼容状态。
- Codex 不得代替教研确认证据、完成润色或作最终批准。

## 技术契约

- [架构边界](docs/architecture.md)
- [HTTP API](docs/api.md)
- [MCP 工具](docs/mcp-tools.md)
- [题目数据结构](docs/data-schema.md)
- [V2 工作流](docs/workflow-v2.md)
- [检索契约](docs/retrieval-contract.md)

## macOS M3

正式目标设备是 Apple Silicon M3、macOS 14 或更高，计划安装到 `~/CAMS考试工作台`。当前只有构建脚本，没有经过验收的 arm64 Python、wheelhouse、精确锁文件或最终 `.tar.gz`。Windows 测试不能替代 M3 验收，详情见 [macOS 构建说明](scripts/macos/README.md)。
