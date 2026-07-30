# 脚本

本目录包含 Windows 开发、Windows 离线/portable 和 macOS M3 构建脚本。不同脚本服务于不同交付目标，不能混用其验收结论。

## Windows 开发

- `setup.ps1`：创建 `.venv`、安装 `backend/requirements.txt`、复制/下载 BGE-M3 并尝试加载模型。依赖未锁定，且不执行 `encode` 或真实检索。
- `start-web.ps1`：解析模型路径并启动 `backend/api.py`，默认端口 8765。
- `start-mcp.ps1`：解析模型路径并启动 stdio MCP。
- `model-path.ps1`：模型路径优先级辅助函数。

## Windows 交付辅助

- `build-offline-bundle.ps1`：下载 wheelhouse 并复制模型，供 `setup.ps1 -OfflineBundle` 使用。当前按宽范围依赖下载，不是可复现锁定包。
- `build-portable-package.ps1`：复制 Windows Python、site-packages、模型和源码，生成目录或 `.tar.gz`。目标目录已存在时会递归删除，运行前必须核对路径。
- `portable/`：生成包内启动器和中文使用说明。Windows portable 只作为开发测试辅助能力，尚未正式验收。

## macOS M3

`macos/` 包含首次配置、启动、环境检查、修复和构建脚本，目标为 macOS 14+ 的 M3 iMac。当前缺少 arm64 runtime、wheelhouse 和锁文件，详见 [macOS README](macos/README.md)。

## 安全边界

- 构建脚本可能覆盖或删除明确指定的输出目录；不要把工作台根目录或题库目录作为输出路径。
- 安装、修复和升级前应先备份可变数据。
- 安装成功、依赖可导入、模型文件存在都不能替代真实检索验收。
- 当前没有停止服务、可靠端口身份检查、升级或恢复脚本。
