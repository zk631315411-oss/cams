# P2A section probe v3: non-contiguous core_point handling

## 目标

v2 已验证：完整 section 原文锚点 + 候选 function_type 表，可以稳定抽取连续主题块内的 core_point。

v3 测试新增能力：同一 section 内，如果前后分散的 units 讲同一复习主题，中间穿插案例、背景或列表，P2A 是否可以把非连续 units 合成同一个 core_point，并明确标记不连续来源。

## 保持不变的规则

1. 输入仍然直接给完整 section 原文锚点。
2. 输入仍然给候选 function_type 列表。
3. 不给每个 unit 的旧 `type`、`unit_type`、`old_type`。
4. unit function type 必须从候选表中选择。
5. P2A 仍只输出 core_point 节点草案，不输出正式 `core_point -> unit` 角色边。

## 新增规则

允许同一 section 内非连续 units 组成一个 core_point，但必须输出：

```text
source_unit_spans
non_contiguous
intervening_unit_ids
review_flags
```

如果 `non_contiguous=true`，必须说明：

1. 为什么前后 units 属于同一复习主题。
2. 中间 units 为什么不属于该 core_point，或只是插入案例/背景。
3. 是否需要人工确认。

## 质量判断

好的 v3 输出不是强行制造非连续 core_point。只有真实同主题回返时才应使用 `non_contiguous=true`。

如果 section 内所有合理 core_point 都连续，也应输出连续 core_point，并在报告中说明未发现需要非连续合并的主题。

