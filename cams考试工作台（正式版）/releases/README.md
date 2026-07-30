# 发布包

`releases` 保存由 `WorkspaceStore.build_release` 生成的不可变快照。当前目录没有任何正式发布包。

## 规则

- `release_id` 必须匹配 `v7-[A-Za-z0-9._-]+`。
- 同名发布目录已存在时构建失败，不允许覆盖。
- 构建期间使用全局发布锁，并尝试锁定每道题。
- V2 题目只有在 `release_ready / active`，且证据确认、正式解析、最终核验和人工批准绑定当前版本时才会进入发布包。
- 当前代码仍有无 `workflow.json` 时的旧发布回退分支，属于 Deprecated 兼容能力。

## 文件

- `questions.json`：题面及 V2 正式解析。
- `evidence.json`：证据确认和被候选版本引用的证据。
- `approved_questions.json`：每题绑定的题面、证据确认、解析、最终核验和决定版本。
- `manifest.json`：发布 ID、创建时间、操作者、数量及三个内容文件的结构化 SHA-256。

成功构建后，包含的 V2 题目进入 `released` 并记录 `release_id` 和审计事件。当前没有发布回滚或撤销工具；不得手工修改已生成目录。
