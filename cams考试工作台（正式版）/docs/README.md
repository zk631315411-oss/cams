# 文档索引

本目录保存当前技术契约、交接状态、历史兼容说明和配置示例。文档描述必须与实际代码和测试一致；发生冲突时，以当前代码、测试结果和数据文件为当前行为依据，规划内容必须显式标记为“待实现”。

## 当前规范

- [architecture.md](architecture.md)：V2 架构、模块边界和写入约束。
- [api.md](api.md)：HTTP API 路由和请求约束。
- [mcp-tools.md](mcp-tools.md)：MCP `2.1.0` 的 19 个工具。
- [data-schema.md](data-schema.md)：题目档案、版本、审计和发布结构。
- [workflow-v2.md](workflow-v2.md)：正式阶段、任务状态和版本失效规则。
- [retrieval-contract.md](retrieval-contract.md)：一般检索、题目检索、资产和参数。
- [新题接收与准入-MVP.md](新题接收与准入-MVP.md)：当前已实现的新题归档和重复检查入口。
- [实习生项目导览.md](实习生项目导览.md)：按 V2 更新的低门槛项目导览。

## 交接状态

- [开发交接说明.md](开发交接说明.md)：2026-07-30 的代码、数据和环境基线。
- [已知问题与后续任务.md](已知问题与后续任务.md)：未实现能力、已知故障和接手者待判断事项。

交接状态文档记录某个日期的事实，不能替代模块 README 或接口契约。

## 配置示例

- [macos-project-mcp-config.example.toml](macos-project-mcp-config.example.toml)：当前 Codex 项目级 MCP 配置模板；必须在目标机器生成绝对路径。
- [mcp-config.example.json](mcp-config.example.json)：历史或其他 MCP 客户端格式，不是当前 Codex 正式配置。

## 维护规则

1. 改动 API、MCP 工具、工作流状态、题目文件或检索参数时，同一提交必须更新相应契约。
2. README 只写已经存在的入口；未来能力放入《已知问题与后续任务》。
3. 兼容旧流程的接口必须标记 `Deprecated`，不得继续作为新功能示例。
4. 不在文档中写入 API Key、用户私密目录或无法移植的机器绝对路径。
5. 发布“可用”“ready”或“解压即用”结论前，必须有对应平台和真实依赖的验收证据。
