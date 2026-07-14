# P7D Edge Review v1 Results

## v23：section级追加式Coverage回归（2026-07-13）

产物：

```text
P7C: phases/P7C/outputs/ds_pro_none_additive_coverage_v23_10sections
P7D: phases/P7D/outputs/p7d_additive_coverage_v23_10sections
```

```text
sections: 10/10 ok
P7C cards: 26
Coverage new cards: 6
Coverage supplemented cards: 8
Coverage contract errors: 0

P7D cards pass/fail: 17/9
P7D edges accepted/pending/rejected: 37/6/9
Coverage-added edges accepted/pending/rejected: 12/3/6
```

追加式Coverage可以跨候选发现新关系、向已有card追加节点和边，同时不能删除或改写首次抽取内容。KG负例`CH03-S02`保持0卡。`CH06-S09`的PEP评估因素和“卸任后仍可能保持影响力”参照边、`CH06-S10`的高风险阈值条件、`CH08-S05`的限定性风险缓解结果，以及`CH12-S04`的监控结果和CDD参与方输入均获得P7D接受。

新增噪声也被P7D按边拦截：`CH03-S07`的红旗到升级串接、`CH07-S03`的账户关闭到核销先后、`CH12-S04`中丢失情态的宽泛控制效果均未进入答案边。`CH05-S04`的“法规错位—持续更新”被Coverage恢复为候选，但P7D认为两句仅相邻、方向证据不足而拒绝；对应原子规则仍由KG承接。

## v20：输入精简与 Coverage 补丁合同回归（2026-07-13）

产物：

```text
P7C: phases/P7C/outputs/ds_pro_none_input_contract_v20_10sections
P7D: phases/P7D/outputs/p7d_input_contract_v20_10sections
P7D semantic retry: phases/P7D/outputs/p7d_input_contract_v20_semantic_retry
archive: archives/p7c_p7d_input_contract_v16_v19_20260713_100615
```

样本为 `CH02-S04`、`CH03-S02`、`CH03-S07`、`CH05-S04`、`CH06-S09`、`CH06-S10`、`CH07-S03`、`CH08-S05`、`CH12-S04`、`CH47-S04`，P7C 与 P7D 均按 10 并发运行。

```text
P7C sections: 10/10 ok
P7C cards: 19
P7C edges: 29
Coverage candidates reviewed: 50
Coverage promoted cards: 1
Coverage contract errors: 0
legacy card/edge fields: 0
missing derivation: 0

P7D initial cards pass/fail: 15/4
P7D initial edges accepted/pending/rejected: 24/1/4

P7D semantic retry cards pass/fail: 2/2 (4 selected cards)
P7D semantic retry edges accepted/pending/rejected: 6/1/2
```

语义小修后，`CH08-S05` 的“EDD 有助于降低风险”保留限定词后通过，证明限定性控制效果不应因使用 `PRODUCES` 被机械拒绝。`CH06-S10 card_002` 的“监管义务—UBO 计算过程”改为 `pending/llm_inference`，符合关键推理边进入人工复核的要求。

剩余问题不应通过继续放宽 P7D 解决：`CH06-S09 card_003` 把“卸任情境”错误写成采用 PEP 方法之前的 `PRECEDES`；`CH06-S10 card_001` 将阈值说明重复拆卡，两条 `REFERENCES` 缺少足够的局部方向证据，而 `card_002` 已覆盖阈值应用和 UBO 识别流程。`CH02-S04` 的负面新闻到初步调查保持 `pending`，可用于扩展检索但不得进入最终程序断言。

本轮说明输入精简没有造成目标链遗漏：历史漏抽的 `CH06-S09`、`CH06-S10`、`CH07-S03`、`CH08-S05`，以及资产管理链 `CH12-S04`、动态调优链 `CH47-S04` 均已成卡；KG 负例 `CH03-S02` 仍保持 0 卡。Coverage 的无记忆 API 补丁合同稳定，P7D 能独立拦截 P7C 候选噪声。

## 结果

```text
structure: 4/4 cards pass
semantic card result: 0 pass, 4 fail
flow edges: 8
accepted: 2
pending: 3
rejected: 3
API/contract errors: 0
```

这不是审核过严造成的随机失败。3条rejected边集中暴露同一构图问题：原文只规定主体“必须执行动作”，P7C却把同一义务拆成process和X7出口，再写成“动作PRODUCES义务”。义务是动作的规范来源，不是动作产生的结果。

被拒绝的典型结构：

```text
机构必须识别PEP -> PRODUCES -> 识别PEP的义务
机构必须调整监控/KYC并升级 -> PRODUCES -> 调整与升级义务
```

另有一条“监管要求PRECEDES识别动作”被拒绝，因为原文表达的是识别时受标准约束，并非先后步骤。

3条pending边包括：

- 风险偏好导向可选的更高PEP标准
- 执行更高标准导向标准被应用
- “一旦是PEP，永远是PEP”方法导向分类维持

这些边可用于扩展检索，但`answer_eligible=false`，进入人工队列。

2条accepted边分别是：

- 卸任后可能保持影响力 -> 部分机构维持PEP分类方法
- 风险偏好 -> 机构调整交易监控、KYC审查并升级处理

真实试跑证明：结构合法不能替代边级语义审核，P7C的`evidence_strength=explicit`也不能直接作为最终答案放行依据。

## 开放关系合同回归（v16-v18）

### v16：10 section基线

产物：

```text
P7C: phases/P7C/outputs/ds_pro_none_open_relation_v16
P7D: phases/P7D/outputs/p7d_open_relation_v16
```

```text
sections: 10
P7C cards: 18
open_relation: 8
closed_flow: 10
P7D card pass/fail: 10/8
edges: 32
accepted/pending/rejected: 21/3/8
```

四个历史漏抽样本`CH06-S09`、`CH06-S10`、`CH07-S03`、`CH08-S05`均成卡；两个KG负例`CH03-S02`、`CH03-S03`保持0卡。`CH06-S09`的风险偏好约束已正确表达为`process --REFERENCES--> standard`。主要拒绝边仍是静态对象到动作的伪`PRECEDES`、动作到同义结果/审批要求的伪`PRODUCES`。

### v17：静态对象与同义出口修正

产物：

```text
P7C: phases/P7C/outputs/ds_pro_none_open_relation_v17
P7D: phases/P7D/outputs/p7d_open_relation_v17
```

```text
sections: 6
P7C cards: 12
P7D card pass/fail: 6/6
edges: 23
accepted/pending/rejected: 16/2/5
```

同一6 section相较v16，拒绝边由7降至5。`CH05-S02`和`CH08-S05`整卡通过；但单一条件应对仍被审核器误按严格时间顺序拒绝，说明P7C与P7D对`PRECEDES`的逻辑前提语义尚未对齐。

### v18：条件前提与边级反事实检查对齐

产物：

```text
P7C: phases/P7C/outputs/ds_pro_none_open_relation_v18
P7D: phases/P7D/outputs/p7d_open_relation_v18
```

```text
sections: 4
P7C cards: 10
open_relation: 7
closed_flow: 3
P7D card pass/fail: 5/5
edges: 18
accepted/pending/rejected: 9/4/5
```

`CH07-S03`的“若银行知道或怀疑非法资金还贷，则不应接受”已通过：单一条件使用带`condition`的`PRECEDES`，表示逻辑前提而非钟表式先后。`CH03-S07`四张局部卡全部通过，不再把整段案例强行串成单链。P7D也按新规则拒绝了`CH06-S10`中的“识别UBO -> UBO被识别”等同义`PRODUCES`边。

v18仍有5条拒绝边：2条来自`CH05-S04`未保留`typically`且补造适配结果，2条来自`CH06-S10`同义识别结果，1条来自`CH07-S03`把退出情境误写成核销动作的先后。它们说明`thinking=none`下P7C仍会产生候选噪声，但P7D已全部拦截；这些边未进入`answer_eligible`。

## 当前结论

开放式局部关系是必要结构，不需要新增`card_shape`字段，图形形态由P7D根据拓扑派生。P7C召回已覆盖历史漏抽，且不再依赖伪X7出口闭环；但`thinking=none`不能保证逐条遵守语义反事实检查，因此生产链必须保留P7D逐边审核。只有`accepted`边可进入最终证明路径，`pending`边仅用于扩展检索，`rejected`边不可使用。
