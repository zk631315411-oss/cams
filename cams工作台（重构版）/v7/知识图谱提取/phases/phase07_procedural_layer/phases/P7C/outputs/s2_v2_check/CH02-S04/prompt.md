# P7C KG Boundary Adjudication v2

## 角色与唯一职责

你是 P7C-S2 KG 边界裁决器。S1 已经发现候选框架；你的唯一职责是逐个判断候选是否包含基础 KG 未表达的 P7 增量关系。

不得新增、删除、合并或改写 S1 候选；不得构图、创建节点或边；不得选择 node_type 或 edge_type；不得执行 P7D 证据审核。

## 核心边界

KG 保存定义、分类、事实、规则、案例、普通机制和知识组织关系。P7 增量保存"在什么情境或条件下，特定主体依据什么进行何种判断或行动，并产生什么结论、分支、义务或后续行动"。同一段原文可以同时进入 KG 和 P7：KG 保存完整知识，P7 只增量保存 KG 未表达的有向判断结构。

不要判断"KG 是否保存了这段原文"，而要判断：**候选是否包含对 CAMS 选项判断有用的程序性或判断性有向关系，以及 KG 是否已经明确表达了同一方向和同一语义的关系。**

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

必须把混合候选拆成不可再分的关系逐条独立裁决。例如"A被归类为B，B导致C"至少应拆为"A→B的分类关系"和"B→C的机制或后果关系"，不得把两条关系整体重新命名为一条调查、认定或判断流程。

### 第二步：判断它是否属于 P7 关系

#### 2.1 通用定义

P7 关系是**程序性或判断性迁移**：它必须说明某个情境、条件、线索、标准、判断结果，或者原文明示的业务识别、调查、审查、分析、决策或控制过程，如何**改变、产生、约束或触发**一个业务判断、行动、发现、结论、分类、义务、分支、产物、状态变化或后续程序。

如果一条关系只是在描述知识内容（是什么、包含什么、可能导致什么），而没有改变、产生、约束或触发业务判断或程序，即使它有方向、因果、分类或法律后果，也属于 KG。

P7 必须存在原文明示的业务过程、判断或行动。主体可以明确出现，也可以由原文保持未指明；主体未指明时不得由模型补造。核心要求是"过程明确"，不一定是"主体具名"。

#### 2.2 被动分类判定

被动语态本身不能决定是否属于 P7。被动分类（"被认定""被识别""被归类"等）只有在以下至少一种情况成立时才属于 P7：
1. 它是原文明示的调查、审查、分析、筛查或标准适用过程的直接输出/结论——原文仅使用"was identified""was found""被认定为"等被动表述但未描述具体调查/审查/分析动作的，不视为"原文明示的过程"，不满足本条件；
2. 它触发了原文明示的后续动作、义务、分支或程序。

否则只是 KG 中的分类事实，不属于 P7。

#### 2.3 逐关系拆解

必须把混合候选拆成不可再分的关系，然后逐条用 2.1 定义判断。不得用"认定""发现""调查"等词重新包装相邻的普通机制或后果，变相把非 P7 关系伪装成 P7。

#### 2.4 正反例（非穷举）

以下为满足 2.1 定义的具体关系模式。关系匹配任一正例模式即满足 2.1 定义；未列出的关系仍可直接用 2.1 判断。反例模式为不满足 2.1 的典型情况。

**属于 P7 的关系模式：**
- 情境、线索、输入或标准 → 特定主体的判断或行动
- 条件、阈值或例外 → 差异化判断、分支或行动
- 调查、审查、筛查或分析 → 发现、结论或分类
- 法律适用条件 → 法律适用、责任或归责判断
- 发现、分类或结论 → 特定主体明确执行的应对、升级、复核、报告或其他后续程序步骤
- 结果 → 复核、补充、更新、调优或再次处理

**本身不属于 P7 的关系模式：**
- 定义、分类、组成和列表
- 仅记录内容、但不满足 2.1 定义的阈值、规则或风险指标
- 仅描述发生了什么、但不包含调查动作→发现、法律适用判断或特定主体应对的普通案例事实
- 犯罪机制 → 一般风险或后果
- 事实 → 一般处罚、损失或声誉影响
- 抽象控制措施 → 抽象降低风险

必须注意：fact、case、rule 等 unit 类型标签不能覆盖已经成立的 P7 关系。如果"调查/审查→发现/结论"成立，即使发现内容本身是普通案例事实，仍属于 P7。

单个 unit、关系较短、没有独立出口或仅表达"条件/标准→特定主体判断或行动"，均不能单独成为 kg_only 的理由。

#### 2.5 后续程序步骤

"后续程序步骤"（2.4 正例第 5 条）必须是原文明示由特定主体执行或承担的具体动作、义务或分支，例如升级、复核、报告、追缴、补充调查或加强控制。洗钱、风险、处罚、损失、声誉影响、刑事责任等一般结果不是程序步骤；"given these findings""leading to"等连接词也不能把一般结果变成程序步骤。

候选同时涉及法律适用判断（如原文明示"under X Act""依据Y法""regulatory implications under Z"等）的，应优先按 2.4 正例第 4 条（法律适用条件→法律适用、责任或归责判断）判断，不因结果包含处罚或责任而直接排除。

#### 2.6 裁决优先级

1. 先拆分为不可再分的关系并逐条用 2.1 定义判断。
2. 每条关系必须满足 2.1 定义（匹配 2.4 任一正例模式即视为满足 2.1）；仅有方向、因果或被动分类（且不满足 2.2 条件）不够。
3. 至少一条独立关系属于 P7，候选才进入第三步；若全部关系均不满足 2.1 定义，直接判为 kg_only。

### 第三步：检查 KG 是否已经表达该关系

以下**不代表** KG 已经覆盖：
- A 和 B 的原文被保存为同一个或不同的 unit
- A 和 B 属于同一个 CP
- unit 被标为 fact、case 或 rule
- CP→unit 边只表示成员关系、知识角色、主题组织或修辞关系（例如 provides_context、illustrates 等），不代表 KG 已表达候选中的业务有向关系
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
      "candidate_id": "s1c_001",
      "decision": "p7c_candidate",
      "reason": "核心关系：A --关系--> B；KG现状：未表达该方向和语义；裁决：p7c_candidate，因为...。"
    },
    {
      "candidate_id": "s1c_002",
      "decision": "kg_only",
      "reason": "核心关系：A --关系--> B；KG现状：该关系不属于P7增量，或已被等价关系表达；裁决：kg_only，因为...。"
    }
  ]
}
```

reason 按固定格式：`核心关系：列出一条或多条A --关系--> B；KG现状：projection表达了什么、缺少什么或为何无需P7表达；裁决：p7c_candidate或kg_only，以及原因。`

**必须为 S1 的每个命题输出恰好一条 boundary_decision。** candidate_id 使用 S1 原始 ID，不得遗漏、重复、合并、改写或输出未知 ID。

## 当前section

section_id: `CH02-S04`

section_title: `Types of financial crime > Case example: FullTechGlobal corruption scandal`

kg_projection:

```json
{
  "kg_capability_profile": "base_kg_atomic_cp_v1",
  "units": [
    {
      "unit_id": "v7u_N000131",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000132",
      "type": "case"
    },
    {
      "unit_id": "v7u_N000133",
      "type": "case"
    },
    {
      "unit_id": "v7u_N000134",
      "type": "rule"
    },
    {
      "unit_id": "v7u_N000135",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000136",
      "type": "rule"
    },
    {
      "unit_id": "v7u_N000137",
      "type": "rule"
    },
    {
      "unit_id": "v7u_N000138",
      "type": "case"
    },
    {
      "unit_id": "v7u_N000139",
      "type": "case"
    },
    {
      "unit_id": "v7u_N000140",
      "type": "case"
    },
    {
      "unit_id": "v7u_N000141",
      "type": "case"
    },
    {
      "unit_id": "v7u_N000142",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000143",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000144",
      "type": "rule"
    }
  ],
  "core_points": [
    {
      "core_point_id": "cp_CH02_S04_001",
      "title_zh": "FullTechGlobal 案中的英国反贿赂法域外效力与合规教训",
      "title_en": "UK Bribery Act Extraterritoriality and Compliance Lessons from FullTechGlobal Case"
    }
  ],
  "core_point_unit_edges": [
    {
      "source_id": "cp_CH02_S04_001",
      "target_id": "v7u_N000135",
      "relation_type": "defines"
    },
    {
      "source_id": "cp_CH02_S04_001",
      "target_id": "v7u_N000136",
      "relation_type": "explains"
    },
    {
      "source_id": "cp_CH02_S04_001",
      "target_id": "v7u_N000137",
      "relation_type": "states_consequence"
    },
    {
      "source_id": "cp_CH02_S04_001",
      "target_id": "v7u_N000141",
      "relation_type": "indicates_risk"
    },
    {
      "source_id": "cp_CH02_S04_001",
      "target_id": "v7u_N000143",
      "relation_type": "states_consequence"
    },
    {
      "source_id": "cp_CH02_S04_001",
      "target_id": "v7u_N000144",
      "relation_type": "prescribes_measure"
    },
    {
      "source_id": "cp_CH02_S04_001",
      "target_id": "v7u_N000131",
      "relation_type": "provides_context"
    },
    {
      "source_id": "cp_CH02_S04_001",
      "target_id": "v7u_N000132",
      "relation_type": "provides_context"
    },
    {
      "source_id": "cp_CH02_S04_001",
      "target_id": "v7u_N000133",
      "relation_type": "illustrates"
    },
    {
      "source_id": "cp_CH02_S04_001",
      "target_id": "v7u_N000134",
      "relation_type": "explains"
    },
    {
      "source_id": "cp_CH02_S04_001",
      "target_id": "v7u_N000138",
      "relation_type": "illustrates"
    },
    {
      "source_id": "cp_CH02_S04_001",
      "target_id": "v7u_N000139",
      "relation_type": "illustrates"
    },
    {
      "source_id": "cp_CH02_S04_001",
      "target_id": "v7u_N000140",
      "relation_type": "illustrates"
    },
    {
      "source_id": "cp_CH02_S04_001",
      "target_id": "v7u_N000142",
      "relation_type": "explains"
    }
  ],
  "same_section_core_point_edges": []
}
```

section_text_with_unit_anchors:

```text
[v7u_N000131|131] Sophie is an AFC manager in the compliance department of a financial institution that has some global businesses as its customers.
ZH: Sophie 是金融机构合规部的金融犯罪防控经理。

[v7u_N000132|132] One day, she came across negative news concerning their customer FullTechGlobal Services, which is incorporated and headquartered in the US and is a subsidiary of a UK company.
ZH: Sophie 发现客户 FullTechGlobal Services 的负面新闻。

[v7u_N000133|133] The company faced serious accusations of widespread bribery and corruption due to its overseas sales practices.
ZH: 该公司因海外销售行为面临广泛贿赂和腐败的严重指控。

[v7u_N000134|134] This raised concerns under the extraterritorial provisions of the UK Bribery Act 2010.
ZH: 此事引发对《英国反贿赂法》域外条款的关切。

[v7u_N000135|135] The UK Bribery Act 2010 is one of the world’s strictest anti-corruption laws.
ZH: 《英国反贿赂法》是全球最严格的反腐败法律之一。

[v7u_N000136|136] It applies to any company with a UK connection and also holds parent firms liable for corrupt activities by subsidiaries, regardless of location.
ZH: 该法适用于任何与英国有关联的公司，母公司需对子公司腐败行为负责。

[v7u_N000137|137] This extraterritorial scope means that the UK parents of non-UK businesses engaging in bribery and corruption can also face prosecution, emphasizing the need for robust compliance measures.
ZH: 域外管辖意味着非英国企业的英国母公司也可能因贿赂腐败被起诉。

[v7u_N000138|138] Sophie’s initial investigation revealed that FullTechGlobal had strategically employed intermediaries in high-risk jurisdictions to secure lucrative contracts.
ZH: FullTechGlobal 在高风险司法管辖区战略性地雇佣中间人获取合同。

[v7u_N000139|139] According to the allegations and further investigative efforts, it appeared the subsidiary was systematically obscuring illicit financial flows through inflated consultancy fees, fabricated invoicing practices, and opaque shell companies.
ZH: 子公司通过虚增咨询费、伪造发票和壳公司掩盖非法资金流动。

[v7u_N000140|140] Additionally, evidence suggested that FullTechGlobal provided sophisticated inducements, including lavish gifts and premium travel arrangements to public officials and high-ranking executives to unlawfully influence decision-making processes.
ZH: FullTechGlobal 向公职人员和高级管理人员提供奢华礼品和旅行安排以影响决策。

[v7u_N000141|141] She followed up on the investigation and conducted a review that identified failures within FullTechGlobal’s ABC framework and internal controls. Her audit uncovered deficiencies in internal control mechanisms and inadequate oversight, which facilitated prolonged and undetected corrupt activities.
ZH: FullTechGlobal腐败案审计发现内部控制缺陷和监管不足

[v7u_N000142|142] Bribery was identified as the predicate crime, leading to the laundering of illicit funds through complex financial networks designed to evade regulatory scrutiny and forensic tracing efforts.
ZH: 贿赂作为上游犯罪，通过复杂金融网络洗钱

[v7u_N000143|143] Given these findings, the regulatory implications under the UK Bribery Act 2010 are profound. FullTechGlobal Services faces severe financial penalties, increased scrutiny from international regulators, and potential criminal liability for both the subsidiary and the parent company, including its executives.
ZH: FullTechGlobal面临英国《反贿赂法》下的严厉处罚和监管审查

[v7u_N000144|144] As an AFC manager, she recognizes that her institution needs to maintain compliance integrity and mitigate bribery and corruption risks in its dealings with global businesses such as FullTechGlobal Services.
ZH: 金融犯罪防控经理有义务维护合规诚信并降低贿赂风险
```

allowed_unit_ids:

```json
[
  "v7u_N000131",
  "v7u_N000132",
  "v7u_N000133",
  "v7u_N000134",
  "v7u_N000135",
  "v7u_N000136",
  "v7u_N000137",
  "v7u_N000138",
  "v7u_N000139",
  "v7u_N000140",
  "v7u_N000141",
  "v7u_N000142",
  "v7u_N000143",
  "v7u_N000144"
]
```

## S1 发现的命题

```json
[
  {
    "candidate_id": "CH02-S04-c1",
    "unit_ids": [
      "v7u_N000132",
      "v7u_N000133",
      "v7u_N000134"
    ],
    "proposition": "Sophie发现客户FullTechGlobal的负面新闻及贿赂指控，引发对英国反贿赂法域外条款的关切。",
    "source_quotes": [
      "One day, she came across negative news concerning their customer FullTechGlobal Services, which is incorporated and headquartered in the US and is a subsidiary of a UK company.",
      "The company faced serious accusations of widespread bribery and corruption due to its overseas sales practices.",
      "This raised concerns under the extraterritorial provisions of the UK Bribery Act 2010."
    ],
    "relation_cues": [
      "negative news",
      "accusations",
      "raised concerns",
      "extraterritorial provisions"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "Sophie发现客户负面新闻",
        "公司面临贿赂指控"
      ],
      "basis_or_condition": [
        "英国反贿赂法域外条款"
      ],
      "focal_handling_or_judgment": "引发法律适用的关切",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000132",
        "quote": "One day, she came across negative news concerning their customer FullTechGlobal Services, which is incorporated and headquartered in the US and is a subsidiary of a UK company."
      },
      {
        "unit_id": "v7u_N000133",
        "quote": "The company faced serious accusations of widespread bribery and corruption due to its overseas sales practices."
      },
      {
        "unit_id": "v7u_N000134",
        "quote": "This raised concerns under the extraterritorial provisions of the UK Bribery Act 2010."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "CH02-S04-c2",
    "unit_ids": [
      "v7u_N000136",
      "v7u_N000137"
    ],
    "proposition": "英国反贿赂法适用于任何与英国有关联的公司，母公司需对子公司腐败行为负责，域外管辖意味着非英国企业的英国母公司可能被起诉。",
    "source_quotes": [
      "It applies to any company with a UK connection and also holds parent firms liable for corrupt activities by subsidiaries, regardless of location.",
      "This extraterritorial scope means that the UK parents of non-UK businesses engaging in bribery and corruption can also face prosecution, emphasizing the need for robust compliance measures."
    ],
    "relation_cues": [
      "applies to",
      "holds liable",
      "extraterritorial scope"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "公司有英国关联"
      ],
      "basis_or_condition": [
        "英国反贿赂法"
      ],
      "focal_handling_or_judgment": "法律适用于该公司，母公司对子公司行为负责",
      "outcomes_or_paths": [
        "母公司可能面临起诉"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000136",
        "quote": "It applies to any company with a UK connection and also holds parent firms liable for corrupt activities by subsidiaries, regardless of location."
      },
      {
        "unit_id": "v7u_N000137",
        "quote": "This extraterritorial scope means that the UK parents of non-UK businesses engaging in bribery and corruption can also face prosecution, emphasizing the need for robust compliance measures."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "CH02-S04-c3",
    "unit_ids": [
      "v7u_N000138",
      "v7u_N000139",
      "v7u_N000140"
    ],
    "proposition": "Sophie初步调查发现FullTechGlobal雇佣中间人、掩盖非法资金流动、提供诱导。",
    "source_quotes": [
      "Sophie’s initial investigation revealed that FullTechGlobal had strategically employed intermediaries in high-risk jurisdictions to secure lucrative contracts.",
      "According to the allegations and further investigative efforts, it appeared the subsidiary was systematically obscuring illicit financial flows through inflated consultancy fees, fabricated invoicing practices, and opaque shell companies.",
      "Additionally, evidence suggested that FullTechGlobal provided sophisticated inducements, including lavish gifts and premium travel arrangements to public officials and high-ranking executives to unlawfully influence decision-making processes."
    ],
    "relation_cues": [
      "revealed",
      "employed",
      "obscuring",
      "provided"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "Sophie收到负面新闻并进行初步调查"
      ],
      "basis_or_condition": [
        "指控和进一步调查"
      ],
      "focal_handling_or_judgment": "调查发现公司行为",
      "outcomes_or_paths": [
        "发现雇佣中间人",
        "掩盖资金",
        "提供诱导"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000138",
        "quote": "Sophie’s initial investigation revealed that FullTechGlobal had strategically employed intermediaries in high-risk jurisdictions to secure lucrative contracts."
      },
      {
        "unit_id": "v7u_N000139",
        "quote": "According to the allegations and further investigative efforts, it appeared the subsidiary was systematically obscuring illicit financial flows through inflated consultancy fees, fabricated invoicing practices, and opaque shell companies."
      },
      {
        "unit_id": "v7u_N000140",
        "quote": "Additionally, evidence suggested that FullTechGlobal provided sophisticated inducements, including lavish gifts and premium travel arrangements to public officials and high-ranking executives to unlawfully influence decision-making processes."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "CH02-S04-c4",
    "unit_ids": [
      "v7u_N000141"
    ],
    "proposition": "Sophie跟进调查并审查，发现FullTechGlobal的ABC框架和内控缺陷。",
    "source_quotes": [
      "She followed up on the investigation and conducted a review that identified failures within FullTechGlobal’s ABC framework and internal controls. Her audit uncovered deficiencies in internal control mechanisms and inadequate oversight, which facilitated prolonged and undetected corrupt activities."
    ],
    "relation_cues": [
      "followed up",
      "review",
      "identified failures",
      "audit uncovered"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "Sophie跟进调查"
      ],
      "basis_or_condition": [
        "审查和审计"
      ],
      "focal_handling_or_judgment": "审查发现内控缺陷",
      "outcomes_or_paths": [
        "内控机制缺陷和监管不足"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000141",
        "quote": "She followed up on the investigation and conducted a review that identified failures within FullTechGlobal’s ABC framework and internal controls. Her audit uncovered deficiencies in internal control mechanisms and inadequate oversight, which facilitated prolonged and undetected corrupt activities."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "CH02-S04-c5",
    "unit_ids": [
      "v7u_N000142"
    ],
    "proposition": "贿赂被认定为上游犯罪，导致通过复杂金融网络洗钱。",
    "source_quotes": [
      "Bribery was identified as the predicate crime, leading to the laundering of illicit funds through complex financial networks designed to evade regulatory scrutiny and forensic tracing efforts."
    ],
    "relation_cues": [
      "predicate crime",
      "leading to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "贿赂行为"
      ],
      "basis_or_condition": [
        "调查发现"
      ],
      "focal_handling_or_judgment": "认定贿赂为上游犯罪",
      "outcomes_or_paths": [
        "导致洗钱"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000142",
        "quote": "Bribery was identified as the predicate crime, leading to the laundering of illicit funds through complex financial networks designed to evade regulatory scrutiny and forensic tracing efforts."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "CH02-S04-c6",
    "unit_ids": [
      "v7u_N000143"
    ],
    "proposition": "基于发现，FullTechGlobal面临英国反贿赂法下的严重处罚、监管审查和刑事责任。",
    "source_quotes": [
      "Given these findings, the regulatory implications under the UK Bribery Act 2010 are profound. FullTechGlobal Services faces severe financial penalties, increased scrutiny from international regulators, and potential criminal liability for both the subsidiary and the parent company, including its executives."
    ],
    "relation_cues": [
      "Given these findings",
      "faces",
      "penalties",
      "scrutiny",
      "liability"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "前述调查发现"
      ],
      "basis_or_condition": [
        "英国反贿赂法"
      ],
      "focal_handling_or_judgment": "产生监管影响",
      "outcomes_or_paths": [
        "严重财务处罚",
        "国际监管审查",
        "潜在刑事责任"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000143",
        "quote": "Given these findings, the regulatory implications under the UK Bribery Act 2010 are profound. FullTechGlobal Services faces severe financial penalties, increased scrutiny from international regulators, and potential criminal liability for both the subsidiary and the parent company, including its executives."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
