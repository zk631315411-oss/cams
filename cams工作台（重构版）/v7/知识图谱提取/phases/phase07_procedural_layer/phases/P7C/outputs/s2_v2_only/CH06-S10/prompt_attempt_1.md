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

section_id: `CH06-S10`

section_title: `Money Laundering Risks in Financial Services > Control and ownership for AML compliance`

kg_projection:

```json
{
  "kg_capability_profile": "base_kg_atomic_cp_v1",
  "units": [
    {
      "unit_id": "v7u_N000483",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000484",
      "type": "definition"
    },
    {
      "unit_id": "v7u_N000485",
      "type": "definition"
    },
    {
      "unit_id": "v7u_N000486",
      "type": "classification"
    },
    {
      "unit_id": "v7u_N000487",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000488",
      "type": "rule"
    },
    {
      "unit_id": "v7u_N000489",
      "type": "rule"
    },
    {
      "unit_id": "v7u_N000490",
      "type": "rule"
    },
    {
      "unit_id": "v7u_N000491",
      "type": "rule"
    },
    {
      "unit_id": "v7u_N000492",
      "type": "case"
    },
    {
      "unit_id": "v7u_N000493",
      "type": "rule"
    },
    {
      "unit_id": "v7u_N000494",
      "type": "case"
    },
    {
      "unit_id": "v7u_N000495",
      "type": "case"
    },
    {
      "unit_id": "v7u_N000496",
      "type": "rule"
    },
    {
      "unit_id": "v7u_N000497",
      "type": "case"
    }
  ],
  "core_points": [
    {
      "core_point_id": "cp_CH06_S10_001",
      "title_zh": "受益所有人（BO）与最终受益所有人（UBO）",
      "title_en": "Beneficial Owner (BO) vs Ultimate Beneficial Owner (UBO)"
    },
    {
      "core_point_id": "cp_CH06_S10_002",
      "title_zh": "UBO识别要求、门槛及特殊情况",
      "title_en": "UBO Identification Requirements, Thresholds, and Special Cases"
    }
  ],
  "core_point_unit_edges": [
    {
      "source_id": "cp_CH06_S10_001",
      "target_id": "v7u_N000484",
      "relation_type": "defines"
    },
    {
      "source_id": "cp_CH06_S10_001",
      "target_id": "v7u_N000485",
      "relation_type": "defines"
    },
    {
      "source_id": "cp_CH06_S10_001",
      "target_id": "v7u_N000483",
      "relation_type": "provides_context"
    },
    {
      "source_id": "cp_CH06_S10_001",
      "target_id": "v7u_N000486",
      "relation_type": "explains"
    },
    {
      "source_id": "cp_CH06_S10_001",
      "target_id": "v7u_N000487",
      "relation_type": "explains"
    },
    {
      "source_id": "cp_CH06_S10_002",
      "target_id": "v7u_N000488",
      "relation_type": "states_rule"
    },
    {
      "source_id": "cp_CH06_S10_002",
      "target_id": "v7u_N000489",
      "relation_type": "states_rule"
    },
    {
      "source_id": "cp_CH06_S10_002",
      "target_id": "v7u_N000490",
      "relation_type": "prescribes_measure"
    },
    {
      "source_id": "cp_CH06_S10_002",
      "target_id": "v7u_N000491",
      "relation_type": "states_rule"
    },
    {
      "source_id": "cp_CH06_S10_002",
      "target_id": "v7u_N000493",
      "relation_type": "states_rule"
    },
    {
      "source_id": "cp_CH06_S10_002",
      "target_id": "v7u_N000496",
      "relation_type": "states_rule"
    },
    {
      "source_id": "cp_CH06_S10_002",
      "target_id": "v7u_N000492",
      "relation_type": "illustrates"
    },
    {
      "source_id": "cp_CH06_S10_002",
      "target_id": "v7u_N000494",
      "relation_type": "illustrates"
    },
    {
      "source_id": "cp_CH06_S10_002",
      "target_id": "v7u_N000495",
      "relation_type": "illustrates"
    },
    {
      "source_id": "cp_CH06_S10_002",
      "target_id": "v7u_N000497",
      "relation_type": "illustrates"
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH06_S10_001",
      "target_id": "cp_CH06_S10_002",
      "relation_type": "prepares"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000483|483] Control and ownership play a vital role in AML efforts, as they can often be obscured or concealed, allowing bad actors to disguise criminal activities and facilitate financial crime.
ZH: 控制权和所有权在反洗钱工作中至关重要

[v7u_N000484|484] A beneficial owner (BO) is defined as an individual or entity that possesses ownership of a legal entity, either through shareholding or other means.
ZH: 受益所有人（BO）的定义：通过持股或其他方式拥有法律实体的个人或实体

[v7u_N000485|485] In contrast, the ultimate beneficial owner (UBO) refers specifically to one or more natural persons who ultimately owns a substantial percentage of shareholding.
ZH: 最终受益所有人（UBO）的定义：最终持有重大比例股份的自然人

[v7u_N000486|486] It is important to note that a BO might appear to have ownership of a company but might not control the company. Conversely, a UBO might not directly hold shares but does exert ultimate control over it.
ZH: BO 可能拥有所有权但不控制公司，UBO 可能不直接持股但实施最终控制

[v7u_N000487|487] This distinction is crucial when it comes to regulatory requirements surrounding ownership structures.
ZH: BO 与 UBO 的区别对所有权结构的监管要求至关重要

[v7u_N000488|488] When reviewing ownership structures, there is a regulatory obligation to identify the UBO of a customer.
ZH: 监管要求审查所有权结构时必须识别客户的 UBO

[v7u_N000489|489] For AML purposes, most jurisdictions require beneficial ownership to be identified at a threshold of 25% or more. That means you need to know every entity or individual who owns at least 25% of a customer.
ZH: 多数司法管辖区要求识别持股 25% 或以上的受益所有人

[v7u_N000490|490] Your organization will set the appropriate threshold using a riskbased approach.
ZH: 机构应采用风险为本的方法设定受益所有权阈值

[v7u_N000491|491] For certain high-risk customers, the beneficial ownership threshold might be as low as 10% and could go as low as 5% for customers who pose a significantly higher risk.
ZH: 高风险客户的受益所有人阈值可能低至 10% 甚至 5%

[v7u_N000492|492] For example, high-risk financial institutions with correspondent banking relationships in a high-risk jurisdiction might set their threshold at 5%.
ZH: 示例：高风险司法管辖区的代理行关系可能设定 5% 的阈值

[v7u_N000493|493] In order to identify the UBOs of Company A, you need to identify indirect ownership stakes in addition to direct ownership.
ZH: 识别 UBO 需要同时考虑直接和间接持股

[v7u_N000494|494] Individual D owns 10% of Company A directly. They also own 72% of Company A indirectly, as they own 90% of shares of Company B, which owns 80% of Company A. Individual D is then considered a UBO with 82% shareholding of Company A.
ZH: 示例：个人 D 通过直接和间接持股合计 82%，成为 UBO

[v7u_N000495|495] Individual C, who owns 10% of Company A directly and an additional 8% indirectly via their 10% ownership of Company B, is not a UBO.
ZH: 示例：个人 C 直接持股 10% 加间接持股 8%，未达到 UBO 标准

[v7u_N000496|496] In companies where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified. This allows you to understand who is in control of the decision-making in the company when natural individual UBOs are not present.
ZH: 无自然人受益所有人时，应识别并核实控制人或名义受益所有人

[v7u_N000497|497] For example, for a company that is publicly listed on the stock exchange and has thousands of shareholders, a notional beneficial owner could be the president or chief executive officer, or equivalent.
ZH: 示例：上市公司可将总裁或 CEO 作为名义受益所有人
```

allowed_unit_ids:

```json
[
  "v7u_N000483",
  "v7u_N000484",
  "v7u_N000485",
  "v7u_N000486",
  "v7u_N000487",
  "v7u_N000488",
  "v7u_N000489",
  "v7u_N000490",
  "v7u_N000491",
  "v7u_N000492",
  "v7u_N000493",
  "v7u_N000494",
  "v7u_N000495",
  "v7u_N000496",
  "v7u_N000497"
]
```

## S1 发现的命题

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000488",
      "v7u_N000489",
      "v7u_N000493",
      "v7u_N000494",
      "v7u_N000495"
    ],
    "proposition": "审查所有权结构时，监管要求识别UBO；多数司法管辖区以25%为阈值，需同时考虑直接和间接持股；达到阈值认定为UBO，未达到则不认定。",
    "source_quotes": [
      "When reviewing ownership structures, there is a regulatory obligation to identify the UBO of a customer.",
      "For AML purposes, most jurisdictions require beneficial ownership to be identified at a threshold of 25% or more.",
      "In order to identify the UBOs of Company A, you need to identify indirect ownership stakes in addition to direct ownership.",
      "Individual D is then considered a UBO with 82% shareholding of Company A.",
      "Individual C, who owns 10% of Company A directly and an additional 8% indirectly via their 10% ownership of Company B, is not a UBO."
    ],
    "relation_cues": [
      "when",
      "require",
      "threshold",
      "in order to",
      "considered",
      "not"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "审查所有权结构时"
      ],
      "basis_or_condition": [
        "监管要求",
        "25%或以上阈值",
        "直接和间接持股合并计算"
      ],
      "focal_handling_or_judgment": "判断客户持股是否达到UBO认定标准",
      "outcomes_or_paths": [
        "达到阈值：认定为UBO",
        "未达到阈值：不认定为UBO"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000488",
        "quote": "When reviewing ownership structures, there is a regulatory obligation to identify the UBO of a customer."
      },
      {
        "unit_id": "v7u_N000489",
        "quote": "For AML purposes, most jurisdictions require beneficial ownership to be identified at a threshold of 25% or more."
      },
      {
        "unit_id": "v7u_N000493",
        "quote": "In order to identify the UBOs of Company A, you need to identify indirect ownership stakes in addition to direct ownership."
      },
      {
        "unit_id": "v7u_N000494",
        "quote": "Individual D is then considered a UBO with 82% shareholding of Company A."
      },
      {
        "unit_id": "v7u_N000495",
        "quote": "Individual C, who owns 10% of Company A directly and an additional 8% indirectly via their 10% ownership of Company B, is not a UBO."
      }
    ],
    "induction": "cross_unit",
    "cross_unit_basis": {
      "rule_unit_ids": [
        "v7u_N000488",
        "v7u_N000489",
        "v7u_N000493"
      ],
      "positive_example_unit_ids": [
        "v7u_N000494"
      ],
      "negative_example_unit_ids": [
        "v7u_N000495"
      ]
    }
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N000490",
      "v7u_N000491",
      "v7u_N000492"
    ],
    "proposition": "机构采用风险为本方法设定受益所有权阈值；高风险客户阈值可能低至10%甚至5%。",
    "source_quotes": [
      "Your organization will set the appropriate threshold using a riskbased approach.",
      "For certain high-risk customers, the beneficial ownership threshold might be as low as 10% and could go as low as 5% for customers who pose a significantly higher risk.",
      "For example, high-risk financial institutions with correspondent banking relationships in a high-risk jurisdiction might set their threshold at 5%."
    ],
    "relation_cues": [
      "riskbased approach",
      "might",
      "could",
      "for example"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "机构设定受益所有权阈值"
      ],
      "basis_or_condition": [
        "风险为本方法",
        "客户风险水平"
      ],
      "focal_handling_or_judgment": "设定适用的受益所有权阈值",
      "outcomes_or_paths": [
        "默认阈值",
        "高风险客户阈值10%",
        "显著更高风险客户阈值5%"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000490",
        "quote": "Your organization will set the appropriate threshold using a riskbased approach."
      },
      {
        "unit_id": "v7u_N000491",
        "quote": "For certain high-risk customers, the beneficial ownership threshold might be as low as 10% and could go as low as 5% for customers who pose a significantly higher risk."
      },
      {
        "unit_id": "v7u_N000492",
        "quote": "For example, high-risk financial institutions with correspondent banking relationships in a high-risk jurisdiction might set their threshold at 5%."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N000496",
      "v7u_N000497"
    ],
    "proposition": "无自然人受益所有人时，应识别并核实控制人或名义受益所有人；例如上市公司可将总裁或CEO作为名义受益所有人。",
    "source_quotes": [
      "In companies where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified.",
      "For example, for a company that is publicly listed on the stock exchange and has thousands of shareholders, a notional beneficial owner could be the president or chief executive officer, or equivalent."
    ],
    "relation_cues": [
      "where",
      "should",
      "for example",
      "could"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "公司不存在自然人受益所有人"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "识别并核实控制人或名义受益所有人",
      "outcomes_or_paths": [
        "控制人或名义受益所有人被记录"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000496",
        "quote": "In companies where there is no natural beneficial owner, a controller or a notional beneficial owner should be identified and verified."
      },
      {
        "unit_id": "v7u_N000497",
        "quote": "For example, for a company that is publicly listed on the stock exchange and has thousands of shareholders, a notional beneficial owner could be the president or chief executive officer, or equivalent."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
