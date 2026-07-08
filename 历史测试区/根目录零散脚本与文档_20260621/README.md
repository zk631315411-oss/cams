# 根目录零散脚本与文档归档说明

归档时间：2026-06-21

本目录保存原来散落在 `D:\守正公司工作区\cams考试` 根目录下的脚本、文档和重复教材文本。

这些文件当前不属于 CAMS 工作台主线运行入口。为了保持根目录清爽，先统一归档，不删除。

## 仍保留在根目录的文件

`start_cams_workbench.py` 仍保留在根目录。

它是当前有实际用途的本地启动脚本，会尝试启动：

- 工作台前端：`http://127.0.0.1:5173/index.html`
- 新题解析 API：`http://127.0.0.1:8765/api/new-question/health`
- 学生答疑 API：`http://127.0.0.1:8766/api/student-qa/health`

## 已归档文件

### `codex_provider_sync_handoff.md`

Codex / CC Switch provider 同步修复的交接记录。

它和 CAMS 业务数据无关，属于 Codex 环境抢救记录。

### `codex_rescue_patch.py`

Codex / CC Switch provider 修复脚本。

注意：这个脚本会触碰用户目录下的 `.codex`、`.cc-switch` 配置或数据库，不能随便运行。

### `convert_tables.py`

一次性脚本，用于把 `v6教材原文/v6_clean.md` 中部分 HTML 表格转换成普通文本。

当前不是主线脚本。

### `fix_ch3_format_dry_run.py`

第三章 markdown 格式修复的预览脚本，不写回文件。

### `fix_ch3_format.py`

第三章 markdown 格式修复脚本，会写回文件。

这是一次性工具，当前不是主线脚本。

### `planb.md`

早期关于 V6 到 V7 教材版本演化管理的方案文档。

讨论过“以知识点体系作为中间层，管理 v6/v7/v8 教材映射”的思路。

### `v6_clean.md`

根目录下的 V6 教材清洗文本副本。

它与当前主线引用的：

`D:\守正公司工作区\cams考试\v6教材原文\v6_clean.md`

内容一致，因此根目录副本归档。

注意：另一个历史源文件：

`D:\守正公司工作区\cams考试\核心数据\源文\source\v6_clean.md`

与本文件不同，属于更早期的教材清洗源，不在本次归档范围。

## 恢复方式

如后续确实需要恢复某个文件，可从本目录移回：

`D:\守正公司工作区\cams考试`
