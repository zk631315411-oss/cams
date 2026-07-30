# 新题接收与准入 MVP

本文描述当前代码已经实现的新题建档和重复检查。通过准入后，题目进入 V2 `evidence_research`，不再进入必经 DS 草稿流程。

## 当前流程

```text
教研提供文字/PNG/JPG/PDF
-> Codex 调用 create_question_intake
-> 原件与完整性检查
-> duplicate_check
-> Codex 调用 resolve_duplicate_check
-> evidence_research
```

网页不提供手工新建题目接口；`POST /api/questions` 当前明确返回 405。新题只能由 Codex MCP 建档。

## 建档输入

`create_question_intake` 接收：

- `content`：结构化题面，至少包含题干和选项；答案可以未知。
- `intake`：题源类型、来源说明、原始题号或链接、原始文本和答案状态。
- `source_paths`：Codex 可访问的本机 PNG、JPG、JPEG 或 PDF 路径。
- `actor`、`reason`：操作者和建档理由。

单个附件不得超过 20 MB。文件会复制到 `source/files/` 并计算 SHA-256；原始接收信息写入 `source/intake.json`。

## 状态与门禁

- 原件无法归档、格式不支持、文件过大，或题干/选项不完整：旧兼容状态为 `needs_source_clarification`，V2 为 `stage=intake`、`disposition=needs_source_clarification`。
- 完整题目：旧兼容状态为 `duplicate_pending`，V2 为 `stage=duplicate_check`。
- Codex 判断为新题：旧兼容状态写为 `ready_for_ds`，但 V2 正式阶段进入 `evidence_research`。后续代码不得把该旧名称解释成 DS 必经。
- 判断为合并题：V2 处置状态为 `merged`，禁止进入证据研究和发布。
- 待人工判断：保持重复检查阶段。

题源参考答案允许为空，保存为 `answer_status=unknown`。可选 DeepSeek 第二意见的输入不得包含题源答案。

## 重复候选

候选由两层组成：

1. 规范化题干和选项完全一致的候选。
2. 题目间 BM25、可用时的 BGE-M3，以及词面相似度候选。

当前重复判断保存为 `duplicate_check.json`。`merge` 只有自由文本理由，没有结构化 `merge_target_question_id`，这是已知缺口。

## 题号

题号在全局题号锁内扫描现存 `v7_q_######` 的最大编号并加一。并发建档不会得到重复编号。

当前实现没有独立的持久化序列：若人工删除最大编号题目目录，该编号可能再次被分配。因此当前代码不能承诺“题号永不复用”，正式题目目录不得手工删除。

## 已知未完成

- `needs_source_clarification` 后没有正式的补附件或修复 intake 的 API/MCP。
- 合并题没有结构化保存目标题号。
- BGE-M3 当前真实加载失败时，重复候选会退化为 BM25/词面方式。
- 旧 `ready_for_ds`、DS 草稿和 Codex 核验方法仍存在于兼容代码中，待确认无外部调用者后删除。

以上问题只记录现状，本轮文档整理不新增处理方案。
