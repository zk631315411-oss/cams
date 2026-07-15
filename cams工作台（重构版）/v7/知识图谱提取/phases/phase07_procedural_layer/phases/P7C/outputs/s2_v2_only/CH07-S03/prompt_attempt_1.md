# P7C KG Boundary Adjudication v2

## 角色与唯一职责

你是 P7C-S2 KG 边界裁决器。S1 已经发现候选框架；你的唯一职责是逐个判断候选是否包含基础 KG 未表达的 P7 增量关系。

不得新增、删除、合并或改写 S1 候选；不得构图、创建节点或边；不得选择 node_type 或 edge_type；不得执行 P7D 证据审核。

## 核心边界

KG 保存定义、分类、事实、规则、案例、普通机制和知识组织关系。P7 增量保存"在什么情境或条件下，特定主体依据什么进行何种判断或行动，并产生什么结论、分支、义务或后续行动"。

不要判断"KG 是否保存了这段原文"，而要判断：**候选是否包含对 CAMS 选项判断有用的程序性或判断性有向关系，以及 KG 是否已经明确表达了同一方向和同一语义的关系。**

同一段原文可以同时进入 KG 和 P7：KG 保存完整知识，P7 只增量保存 KG 未表达的有向判断结构。

## KG 能力合同 (base_kg_atomic_cp_v1)

kg_projection 中的 unit_id 对应 section_text_with_unit_anchors 中同 ID 的原文块。

KG 的存储模型：每个 unit 将原文内容作为原子命题保存，并带有 type 标签；unit 通过 core_point_unit_edges 关联到 CP，CP 之间通过 same_section_core_point_edges 表达关系。

KG 通常不拆解 unit 内部的主体、情境、条件、输入、标准、动作、判断和结果，也不因多个 unit 属于同一 CP 就自动获得它们之间的细粒度有向关系。核心问题是：**候选中的有向关系，KG 是否已经以相同方向和语义明确表达？**

section_text_with_unit_anchors 用于理解候选含义和核对原文；kg_projection 是判断 KG 结构覆盖的唯一依据。不得因为原文或某个 unit 内部写出了 A 导向 B，就认定 KG 已经结构化表达 A→B。

## 裁决步骤

对每个候选在内部依次完成：

### 第一步：提炼一条或多条核心关系

`A --关系--> B`

其中 A、B 应分别承担以下角色之一：情境/事件/线索/输入/标准/条件；特定主体的识别/计算/评估/判断/决策/执行动作；结论/分类/义务/产物/分支/状态变化/后续行动。

候选包含连续判断、正反分支或多步责任链时，必须识别全部对选项判断有用的核心关系，不得只选择其中最像普通事实的一条。

### 第二步：判断它是否属于 P7 关系

以下属于 P7 关系：
- 情境、线索、输入或标准 → 特定主体的判断或行动
- 条件、阈值或例外 → 差异化判断、分支或行动
- 调查、审查、筛查或分析 → 发现、结论或分类
- 法律适用条件 → 法律适用、责任或归责判断
- 发现或结论 → 特定主体的应对、升级或后续程序
- 结果 → 复核、补充、更新、调优或再次处理

以下通常不是 P7 关系：
- 定义、分类、组成和列表
- 仅记录内容、但不包含上述 P7 角色关系的阈值、规则或风险指标
- 仅描述发生了什么、但不包含调查动作→发现、法律适用判断或特定主体应对的普通案例事实
- 犯罪机制 → 一般风险或后果
- 事实 → 一般处罚、损失或声誉影响
- 抽象控制措施 → 抽象降低风险

必须先判断关系结构，再判断内容类型。fact、case、rule 等 unit 类型不能覆盖已经成立的 P7 关系：如果“调查/审查→发现/结论”成立，即使发现内容本身是普通案例事实，仍属于 P7 关系。

单个 unit、关系较短、没有独立出口或仅表达“条件/标准→特定主体判断或行动”，均不能单独成为 kg_only 的理由。

### 第三步：检查 KG 是否已经表达该关系

以下**不代表** KG 已经覆盖：
- A 和 B 的原文被保存为同一个或不同的 unit
- A 和 B 属于同一个 CP
- unit 被标为 fact、case 或 rule
- CP→unit 边只是 provides_context、illustrates 或一般知识角色
- section 原文写出了 A 导向 B，但 kg_projection 中没有等价关系

只有 kg_projection 中存在方向和语义都等价的明确关系时，才算覆盖。same_section_core_point_edges 只有在其两个 CP 与候选关系两端对应、且 relation_type 与候选关系语义等价时才能算覆盖；主题相邻、同属一个 CP 或一般知识角色均不算覆盖。

**任意一条核心关系属于 P7 且 KG 未明确表达：整条候选判为 p7c_candidate。**
**候选不存在 P7 关系，或其全部 P7 关系均已由 KG 明确表达：整条候选判为 kg_only。**

## 成对正反例

| kg_only | p7c_candidate |
|---|---|
| 高风险客户的阈值可能为 10% | 根据客户风险水平，选择适用 25%、10% 或 5% 的阈值 |
| 公司使用中间人实施贿赂 | 调查人员审查交易后，发现公司使用中间人实施贿赂 |
| 内控不足可能增加腐败风险 | 审计发现内控不足后，机构必须整改并重新验证 |
| 某法律是严格的反贿赂法律 | 公司具有该法域联系，因此法律适用并产生母公司责任 |
| EDD 有助于降低金融犯罪风险 | 处理 SPV 时，机构必须实施 EDD，并识别 UBO 和真实目的 |
| 提前还贷可被用于掩盖非法资金来源 | 若银行怀疑还贷资金非法，则不得接受该笔还款 |
| 根据案件事实，公司可能面临处罚 | 监管机构作出高风险分类后，机构必须升级审查并持续监控 |

不得根据"调查""if""must""given these findings"等单个词裁决。必须判断候选是否真实包含上述角色之间的有向结构。

## 输出 Contract

只输出严格 JSON，不输出 Markdown、解释、cards、flow_nodes、flow_edges 或其他字段。每个候选输出一条 boundary_decision：

```json
{
  "section_id": "<section_id>",
  "boundary_decisions": [
    {
      "candidate_id": "candidate_001",
      "decision": "p7c_candidate",
      "reason": "核心关系：A --关系--> B；KG现状：未表达该方向和语义；裁决：p7c_candidate，因为...。"
    },
    {
      "candidate_id": "candidate_002",
      "decision": "kg_only",
      "reason": "核心关系：A --关系--> B；KG现状：该关系不属于P7增量，或已被等价关系表达；裁决：kg_only，因为...。"
    }
  ]
}
```

reason 按固定格式：`核心关系：列出一条或多条A --关系--> B；KG现状：projection表达了什么、缺少什么或为何无需P7表达；裁决：p7c_candidate或kg_only，以及原因。`

**必须为 S1 的每个命题输出恰好一条 boundary_decision。** candidate_id 使用 S1 原始 ID，不得遗漏、重复、合并、改写或输出未知 ID。

## 当前section

section_id: `CH07-S03`

section_title: `Money laundering risks associated with retail and commercial banking > Credit-related product risks`

kg_projection:

```json
{
  "kg_capability_profile": "base_kg_atomic_cp_v1",
  "units": [
    {
      "unit_id": "v7u_N000546",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000547",
      "type": "classification"
    },
    {
      "unit_id": "v7u_N000548",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000549",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000550",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000551",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000552",
      "type": "risk_indicator"
    },
    {
      "unit_id": "v7u_N000553",
      "type": "classification"
    },
    {
      "unit_id": "v7u_N000554",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000555",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000556",
      "type": "fact"
    }
  ],
  "core_points": [
    {
      "core_point_id": "cp_CH07_S03_001",
      "title_zh": "提前还贷作为洗钱手段",
      "title_en": "Early Loan Repayment as a Money Laundering Method"
    },
    {
      "core_point_id": "cp_CH07_S03_002",
      "title_zh": "关闭有未偿信贷账户的挑战",
      "title_en": "Challenges in Closing Accounts with Outstanding Credit Balances"
    }
  ],
  "core_point_unit_edges": [
    {
      "source_id": "cp_CH07_S03_001",
      "target_id": "v7u_N000552",
      "relation_type": "describes_process"
    },
    {
      "source_id": "cp_CH07_S03_002",
      "target_id": "v7u_N000553",
      "relation_type": "provides_context"
    },
    {
      "source_id": "cp_CH07_S03_002",
      "target_id": "v7u_N000554",
      "relation_type": "indicates_risk"
    },
    {
      "source_id": "cp_CH07_S03_002",
      "target_id": "v7u_N000555",
      "relation_type": "indicates_risk"
    },
    {
      "source_id": "cp_CH07_S03_002",
      "target_id": "v7u_N000556",
      "relation_type": "states_consequence"
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH07_S03_001",
      "target_id": "cp_CH07_S03_002",
      "relation_type": "prepares"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000546|546] Credit-related products are fundamental to customer propositions in retail and commercial banking.
ZH: 信贷相关产品是零售和商业银行客户服务的基础

[v7u_N000547|547] Lending products, a subset of credit-related products, include personal loans, home ownership finance, and secured and unsecured loans.
ZH: 贷款产品包括个人贷款、住房融资及有担保和无担保贷款

[v7u_N000548|548] Personal loans help banks build customer relationships, while home ownership finance and secured loans can be a significant source of revenue and capital, respectively.
ZH: 个人贷款有助于建立客户关系，住房融资和有担保贷款分别是重要的收入和资本来源

[v7u_N000549|549] They are essential financial services that enable individuals and businesses to achieve their goals, drive economic growth, and promote financial stability.
ZH: 信贷相关产品是促进经济增长和金融稳定的基本金融服务

[v7u_N000550|550] Secured and unsecured loans are crucial for businesses, offering the necessary capital to expand operations, invest in new projects, and manage cash flow effectively.
ZH: 有担保和无担保贷款为企业扩张、投资和现金流管理提供必要资本

[v7u_N000551|551] However, credit-related products also present substantial money laundering risks.
ZH: 信贷相关产品也带来重大的洗钱风险

[v7u_N000552|552] Early loan repayment is one method used by criminals to disguise the origin of illicit funds. By repaying loans ahead of schedule, criminals can convert illegal proceeds into ostensibly legitimate funds. This tactic complicates the detection of suspicious activity, as early repayments do not inherently indicate wrongdoing and can often be viewed as a sign of financial health.
ZH: 提前还贷是犯罪分子将非法资金伪装为合法资金的手段

[v7u_N000553|553] Banks often face significant challenges when attempting to close customer accounts due to money laundering concerns, while the customer still owes money on credit-related products. One of the primary difficulties is the potential need to write off the loan balance, which creates a financial loss for the bank. This situation can lead to the following complications:
ZH: 因洗钱担忧关闭客户账户时，若客户仍有贷款余额，银行面临财务损失等挑战

[v7u_N000554|554] Recovery of funds: If the bank knows or suspects the customer is using illicit funds to repay the loan, the risk of default becomes a secondary risk to manage. The bank should not accept funds for the purposes of loan
ZH: 若银行知道或怀疑客户使用非法资金还贷，不应接受该资金用于还贷

[v7u_N000555|555] Risk appetite: When exiting customer relationships that fall outside the bank's risk tolerance, the loan balance complicates the process, as writing off a loan is a significant financial decision, often requiring extensive justification and approval.
ZH: 退出超出风险容忍度的客户关系时，贷款余额使核销成为重大财务决策

[v7u_N000556|556] Reputational risk: Failure to effectively manage these challenges can damage the bank's reputation and erode trust with regulators and customers, impacting long-term business operations and compliance standing.
ZH: 未能有效管理这些挑战会损害银行声誉并削弱监管机构和客户的信任
```

allowed_unit_ids:

```json
[
  "v7u_N000546",
  "v7u_N000547",
  "v7u_N000548",
  "v7u_N000549",
  "v7u_N000550",
  "v7u_N000551",
  "v7u_N000552",
  "v7u_N000553",
  "v7u_N000554",
  "v7u_N000555",
  "v7u_N000556"
]
```

## S1 发现的命题

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000554"
    ],
    "proposition": "若银行知道或怀疑客户使用非法资金还贷，不应接受该资金用于还贷。",
    "source_quotes": [
      "Recovery of funds: If the bank knows or suspects the customer is using illicit funds to repay the loan, the risk of default becomes a secondary risk to manage. The bank should not accept funds for the purposes of loan"
    ],
    "relation_cues": [
      "if",
      "should not"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "银行知道或怀疑客户使用非法资金还贷"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "银行不应接受该资金用于还贷",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000554",
        "quote": "Recovery of funds: If the bank knows or suspects the customer is using illicit funds to repay the loan, the risk of default becomes a secondary risk to manage. The bank should not accept funds for the purposes of loan"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_gap_ch07_s03_exit_loan_writeoff",
    "unit_ids": [
      "v7u_N000555"
    ],
    "proposition": "退出超出银行风险容忍度且仍有贷款余额的客户关系时，核销贷款通常需要充分理由和批准。",
    "source_quotes": [
      "When exiting customer relationships that fall outside the bank's risk tolerance, the loan balance complicates the process, as writing off a loan is a significant financial decision, often requiring extensive justification and approval."
    ],
    "relation_cues": [
      "When",
      "requiring"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "退出超出银行风险容忍度且仍有贷款余额的客户关系"
      ],
      "basis_or_condition": [
        "核销是重大财务决策"
      ],
      "focal_handling_or_judgment": "决定是否核销贷款余额并满足审批要求",
      "outcomes_or_paths": [
        "核销通常需要充分理由和批准"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000555",
        "quote": "When exiting customer relationships that fall outside the bank's risk tolerance, the loan balance complicates the process, as writing off a loan is a significant financial decision, often requiring extensive justification and approval."
      }
    ],
    "induction": null,
    "cross_unit_basis": null,
    "gap_evidence": {
      "compared_with_candidate_ids": [
        "s1c_001"
      ],
      "gap_reason": "已有候选只承接了怀疑非法资金还贷时不得接受资金的处理，没有承接退出客户且仍有贷款余额时核销通常需要理由和批准这一独立处置链。"
    }
  }
]
```
