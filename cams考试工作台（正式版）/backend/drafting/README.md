# Drafting 模块

本目录同时存在当前能力和旧兼容链路，名称容易误导。

## 当前能力

`deepseek.py` 提供可选的 DeepSeek 独立第二意见：

- 只能在教研明确确认后调用。
- 输入为当前题面和已选证据快照，不包含题源参考答案。
- 结果保存为辅助研判记录，成功或失败都不推进 V2 正式阶段。
- API Key 保存在用户本机私密配置目录，不写入题库、审计或备份。

正式解析不是本模块自动生成的 DS 草稿。当前 V2 正式解析由 Codex 通过 MCP `write_analysis_version` 写入版本化记录。

## Deprecated 兼容能力

`service.py` 的 `prepare_draft_input` 为旧 DS 草稿流程准备输入，仍依赖旧 `assert_ds_ready` 和 `evidence_review`。它不是当前主线，待接手开发者确认没有外部调用者后，与旧 API/存储方法一起删除。

本轮只记录状态，不删除代码。
