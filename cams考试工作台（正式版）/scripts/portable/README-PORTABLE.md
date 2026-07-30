# CAMS Windows Portable 使用说明

本文件会被复制到生成的 Windows portable 包根目录。该方案只用于开发和测试辅助，不是 M3 iMac 正式交付目标，当前也没有经过完整 portable 验收。

## 预期内容

生成包应包含：

- `runtime/python`：Windows Python 和依赖。
- `runtime/models/bge-m3`：本地模型。
- `backend`、`frontend`、`data`、`scripts`：工作台源码与数据。
- `Start-Web.cmd`、`Start-Codex-MCP.cmd`。
- `manifest.json`：文件 SHA-256 清单。

只有实际生成并验收的包才能声称解压后不需要 Python、pip 或模型下载。

## 使用

1. 校验交付方提供的压缩包和 `manifest.json`。
2. 解压到不再移动的目录。
3. 双击 `Start-Web.cmd`，打开 `http://127.0.0.1:8765`。
4. Codex MCP 使用 `cmd.exe /c <package-root>\Start-Codex-MCP.cmd` 作为 stdio server。

移动目录后需要更新 Codex MCP 的绝对路径。

## 当前限制

- 构建脚本只检查依赖导入，不执行真实 BGE `encode` 或检索。
- 没有停止服务、升级、恢复或可靠端口身份检查。
- 当前 BGE 依赖组合存在真实加载故障。
- 未在全新 Windows 用户环境完成端到端验收。
