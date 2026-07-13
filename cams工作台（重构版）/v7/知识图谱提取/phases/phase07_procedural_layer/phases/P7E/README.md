# P7E：Card Bridge Candidate 生成

## 定位

P7E 读取已通过 P7D 汇报口径的 `p7_card`，生成 card 之间的桥接候选 `p7_bridge_edge`。

P7E 不修改 card 内部的 `flow_nodes` / `flow_edges`，不合并 cluster，不生成 scenario path，也不写考生解析。

## 目标

P7E 只回答一个问题：

```text
哪些 card 之间可能存在可解释的业务连接？
```

这里的连接包括：

```text
一个 card 的 output 可触发另一个 card 的 trigger
一个 risk_indicator / assessment card 的 finding 可作为 execution / control card 的判断依据
一个 control card 的输出可进入 assessment card 评估控制有效性
同一业务流程中前后 section 的局部 card 可形成自然前后关系
```

## 输入

```text
P7C/cards.raw.json
P7D/p7d_review_manifest.jsonl
P6/kg_retrieval_graph.json
```

只使用边级审核汇总后`card_result = pass`的card。旧`review_result = pass`仅作为历史兼容，不再是正式放行口径。

## 输出

```text
outputs/p7e_bridge_candidates.jsonl
reports/p7e_bridge_candidate_report.md
```

## p7_bridge_edge

P7E 输出候选桥接边，不写入 `p7_card.flow_edges`。

```json
{
  "bridge_id": "p7bridge_...",
  "edge_type": "BRIDGES_TO",
  "source_card_id": "p7card_...",
  "target_card_id": "p7card_...",
  "source_node_id": "optional output/decision node",
  "target_node_id": "optional trigger/start/action node",
  "bridge_semantics": "proceeds_to | provides_basis | supports_control | may_trigger",
  "bridge_basis": "shared_unit | lexical_signal | card_nature_logic | section_order | human_review",
  "evidence_unit_ids": ["v7u_..."],
  "source_node_strength": "explicit | functional_dependency | needs_review | rejected",
  "target_node_strength": "explicit | functional_dependency | needs_review | rejected",
  "condition": "optional condition",
  "confidence": "candidate | strong_candidate | needs_review",
  "review_status": "needs_review",
  "notes": "why this bridge may exist"
}
```

## 第一版策略

P7E 第一版先生成候选，不做最终裁判：

```text
1. 只连接P7D边级审核后`card_result = pass`的card。
2. 优先连接同章、相邻 section、或同一业务主题下的 card。
3. 使用 card_nature 约束方向：risk_indicator/assessment 通常作为判断依据，execution/control 通常作为处置路径。
4. 桥接必须保留 source_card_id / target_card_id，必要时保留 source_node_id / target_node_id。
5. 每条候选必须标明 `bridge_semantics`，区分流程后继、判断依据、控制支持和可能触发。
6. 每条候选必须记录 source/target 节点的 evidence_strength；如果任一端是 `functional_dependency`，候选自动降级。
7. 不允许只靠关键词重合生成 `strong_candidate`。
8. 所有候选默认 review_status = needs_review，由后续 review 或人工确认。
9. P7E 先在节点层生成候选，再按 `source_card_id / target_card_id / bridge_semantics` 合并压缩；同一组只保留少量最像接口的候选，避免把一个 card 关系展开成大量内部节点组合。
10. 接口优先级为：source 端优先 `output > decision > end`，target 端优先 `trigger > start > action > standard`。
11. 如果 source 输出表示终止分支，例如 unsuitable / filtered out / rejected / declined，不应继续桥接到后续 execution 流程。
```

主输出 `p7e_bridge_candidates.jsonl` 是压缩后的候选清单。脚本可在候选中记录 `candidate_group_size` 和 `candidate_rank`，用于说明该候选来自多大的节点组合池，以及为什么被保留。

## bridge_semantics

```text
proceeds_to       source 的输出进入 target 的后续流程
provides_basis    source 的风险发现/评估结论为 target 提供判断依据
supports_control  source 的控制/治理结果支持 target 的控制评估或处置
may_trigger       source 可能触发 target，但证据较弱，需要 review
```

## confidence

```text
strong_candidate  方向合理、接口角色匹配、存在明确业务短语重合，且不能只由关键词决定
candidate         方向合理、接口角色匹配，有可解释但较弱的信号
needs_review      方向可能合理，但证据弱、跨度大，或依赖 functional_dependency
```

`confidence` 不是最终审核结果。P7E 不输出 confirmed bridge。

## Review 口径

P7E review 保持轻量：Codex 先判断，再向人工汇报。

```text
card_result = pass  card内所有边均已审核接受，可进入后续实验
card_result = fail  至少一条边pending/rejected或结构失败，不得作为完整已验证card进入后续
```

P7E 不需要复杂处置表。报告中只需说明：候选边是什么、为什么连、证据强弱、Codex 初判 pass/fail。

## 风险控制

P7E v1 是保守候选生成器，不是自动连图器：

```text
词面重合只能作为信号，不能单独证明连接成立
output -> trigger 也可能方向错误，必须记录 notes
assessment / risk_indicator 多数是依据关系，不一定是时间先后
输入 card 不完整时，候选不代表全书完整图
候选边不能污染 p7_card.flow_edges 正本
```

## 非目标

```text
不生成 cluster
不生成 scenario path
不把 bridge 写进 card.flow_edges
不跨越P7D的`card_result`与边级`review_status`约束
不直接用于答题裁判
不生成 confirmed bridge
```
