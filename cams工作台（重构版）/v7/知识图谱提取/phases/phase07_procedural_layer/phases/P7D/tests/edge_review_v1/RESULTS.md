# P7D Edge Review v1 Results

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
