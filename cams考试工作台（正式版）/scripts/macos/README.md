# macOS M3 构建与验收说明

本目录面向接手开发者，目标设备为 Apple Silicon M3、macOS 14 或更高。当前脚本是源码级构建准备，不是已验收交付包。

## 当前缺失

- 可重定位的 CPython 3.11 arm64 runtime 及其来源说明。
- `wheelhouse/macos-arm64` 和经过真实检索验收的 `requirements-macos-arm64.lock`。
- 最终 `.tar.gz`、SHA-256 和干净 M3 账号验收记录。
- 停止服务、端口身份校验、升级、恢复、回滚和卸载实现。

## 脚本

| 文件 | 当前行为 |
| --- | --- |
| `build-package.command` | 在 M3 上复制 runtime、模型和源码，安装/冻结依赖，下载 wheelhouse，生成 manifest 和 tar.gz |
| `首次配置并连接Codex.command` | 复制到 `~/CAMS考试工作台`、移除 quarantine、生成项目级 MCP、检查工具列表并备份 |
| `启动工作台.command` | 后台启动 API 并打开浏览器 |
| `检查环境.command` | 计划导入依赖、检查资产/MCP 并执行真实检索；当前查找已移除的 `write_codex_review`，会在真实检索前失败 |
| `修复运行环境.command` | 先备份，优先离线 wheelhouse；缺失时经用户确认使用清华镜像 |
| `lib.sh` | 平台、路径、runtime、MCP 配置和备份共享函数 |

## 构建

只能在 M3 Mac 上运行：

```bash
export CAMS_MAC_PYTHON_HOME="/absolute/path/to/relocatable-python-3.11-arm64"
export CAMS_MAC_MODEL_PATH="/absolute/path/to/bge-m3"  # 工作台内已有模型时可省略
./scripts/macos/build-package.command
```

脚本会删除并重建以下输出，运行前必须确认路径：

```text
dist/CAMS考试工作台-macos-arm64/
dist/CAMS考试工作台-macos-arm64.tar.gz
```

输出应包含 `runtime/python`、`runtime/models/bge-m3`、`wheelhouse/macos-arm64`、`requirements-macos-arm64.lock` 和 `manifest.sha256`。

当前构建门禁只检查依赖导入，没有执行模型 `encode` 和真实检索；生成文件不等于正式验收通过。

## 首次配置

在准备好的包内双击 `首次配置并连接Codex.command`。默认安装到 `~/CAMS考试工作台`，也可设置 `CAMS_INSTALL_ROOT`。

- 目标目录已存在时不会覆盖，脚本会退出。
- 项目级配置写入安装目录的 `.codex/config.toml`，不会修改全局 `~/.codex/config.toml`。
- 配置使用安装后的绝对路径；移动目录后必须重新生成。
- 无签名脚本可能需要 Control-click 后选择“打开”。脚本会尝试清除安装目录 quarantine 属性。

完成后重新用 Codex 打开安装目录并重启 Codex，使项目级 MCP 生效。

## 当前诊断口径

`检查环境.command` 尚不能作为验收凭据，因为它查找旧 MCP 工具名。修复后应校验 `cams-formal-workbench 2.1.0` 和当前 19 个工具，并执行：

1. 模型 SHA-256。
2. 断网本地模型加载和非空 `encode`。
3. 一般检索与题目检索。
4. MCP `tools/list` 和 `read_active_context`。
5. 网页、题目/PDF、证据、解析、批准和测试发布。
6. 备份及一次真实恢复。

## Gatekeeper 与日志

- 首次授权失败时检查文件是否保留执行权限以及 `com.apple.quarantine`。
- API 启动日志写入 `data/control/api.log`。
- 启动脚本只检查 `/api/health` 是否返回成功，没有核对应用身份；端口被其他服务占用时可能误判。

在上述缺口修复并完成干净 M3 验收前，不得称为“解压即用正式包”。
