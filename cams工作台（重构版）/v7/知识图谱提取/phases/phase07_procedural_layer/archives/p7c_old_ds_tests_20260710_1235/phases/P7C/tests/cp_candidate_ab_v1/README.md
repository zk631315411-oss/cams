# P7C Test: CP Candidate AB v1

## 目的

本实验比较两条 P7C 提取路径：

```text
A 组：section units -> DS -> final P7 cards

B 组：core points + same-section CP edges -> DS round 1 -> flow_node_candidates
     flow_node_candidates + section units -> DS round 2 -> final P7 cards
```

实验要回答的问题不是“CP 能否替代 flow_node”，而是：

```text
把 CP 作为候选召回层，是否能提高 P7 card 的召回率、节点完整性和判断路径稳定性，
同时不显著增加普通 KG 内容误入 P7、虚构流程、错误边或证据漂移。
```

## 核心约束

1. 第一轮只生成 `flow_node_candidates`，不得生成最终 `flow_nodes`、`flow_edges` 或 `cards`。
2. CP 可以进入候选池，但不能直接落库为 P7 `flow_node`。
3. 第二轮可删除、合并、拆分或补充候选，不要求覆盖所有 CP。
4. 第二轮最终证据只能来自当前 section 的 unit。
5. CP-CP 边只用于第一轮理解 CP 之间的组织关系，不能转换为 P7 `flow_edges`。
6. A、B 两组使用相同的最终 P7 schema、相同 section units、相同模型参数和同一 validator。

## 文件

```text
prompts/cp_to_flow_node_candidates_v1.md
    第一轮 DS 提示词：CP -> 节点候选。

prompts/cp_candidate_card_extraction_overlay_v1.md
    第二轮 B 组叠加提示词：候选 + units -> final cards。

run_cp_candidate_ab.py
    AB runner；负责两轮调用、落盘、校验和比较摘要。
```

A 组默认复用：

```text
../card_scope_definition_v1/prompts/section_card_extraction_scope_v1.md
```

## 默认测试集

默认使用当前 scope 实验的 focus6：

```text
CH47-S06
CH49-S13
CH49-S16
CH47-S03
CH47-S04
CH49-S10
```

其中 `CH47-S04` 适合先做 smoke test，因为它同时包含 tuning 目标、并列标准、动态触发和预期控制效果。

## 运行

先做不调用 API 的 prompt dry-run：

```powershell
python run_cp_candidate_ab.py --sections CH47-S04 --run-id dryrun_ch47s04 --dry-run
```

运行单 section AB smoke test：

```powershell
python run_cp_candidate_ab.py --sections CH47-S04 --run-id smoke_ch47s04_ds_none
```

运行 focus6：

```powershell
python run_cp_candidate_ab.py --run-id focus6_ds_none
```

默认读取 `DEEPSEEK_API_KEY`、`DS_API_KEY` 或 `DS_KEY`，默认模型为 `deepseek-v4-pro`，`thinking_effort=none`。

## 输出结构

```text
outputs/<run_id>/
  run_plan.json
  run_summary.json
  run_summary.md
  <section_id>/
    A_direct/
      prompt.md
      raw_response.txt
      cards.raw.json
      validation_report.md
      run_manifest.json
    B_cp_candidates/
      01_candidates/
        prompt.md
        raw_response.txt
        flow_node_candidates.raw.json
        candidate_validation.json
        run_manifest.json
      02_cards/
        prompt.md
        raw_response.txt
        cards.raw.json
        validation_report.md
        run_manifest.json
    ab_comparison.md
```

## 人工审计重点

自动摘要只能比较数量和 validator 结果，不能判断语义质量。人工审计至少检查：

| 维度 | 问题 |
|---|---|
| card scope | B 是否把纯定义、背景或普通事实误抽成 P7？ |
| recall | B 是否恢复了 A 漏掉的 judgement path？ |
| node fidelity | B 的候选是否被合理删除、拆分、合并或补充？ |
| edge fidelity | B 的最终边是否来自 unit 语义，而非 CP-CP `prepares`？ |
| evidence | 每个最终节点和边是否引用当前 section unit？ |
| chronology | 并列标准是否被错误串成 `PRECEDES`？ |
| cost | B 的额外一轮调用是否换来足够质量收益？ |

## 判定建议

B 组只有在以下条件同时成立时才值得进入正式 P7C：

```text
召回率或结构完整性有稳定提升；
普通 KG 内容误入率没有明显上升；
最终 flow_edges 没有被 CP-CP 边污染；
unit 证据绑定不弱于 A；
提升足以覆盖额外调用成本和链路复杂度。
```
