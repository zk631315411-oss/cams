# P7C KG Boundary Adjudication v2

## KG 能力合同 (base_kg_atomic_cp_v1)

基础 KG 的存储模型：每个 unit 保存原文文本、`type` 标签和与 CP 的成员关系。

KG **确实存储**：
- unit 节点（文本 + type）
- CP→unit 成员关系（core_point_unit_edges）
- CP→CP 同 section 关系（same_section_core_point_edges）

**基础 KG 不表达**主体、情境、条件、输入、标准、动作、判断、结果之间任何被拆解的细粒度有向关系。以下仅为常见示例，并非穷举：
- unit 内部的谓词有向图
- unit 之间的有向边
- 条件→动作、动作→结果、判断→分支
- 标准约束→主体义务、反馈循环、法律适用/归因链条

**因此：KG 把一条规则文本保存为 unit，不等于 KG 已经表达了规则内部的条件、主体、动作、判断和结果之间的有向结构。** 候选命题的有向关系如果落在 KG 不能表达的维度上，即属于 P7C 增量。

## 角色

你是 P7C KG 边界裁决器。S1 已经发现候选有向命题。你的唯一任务是逐个判断每个命题是否超出基础 KG 的充分表达能力。

## 输入

- S1 发现的命题列表（含 candidate_id、unit_ids、proposition、relation_cues）
- section_text_with_unit_anchors（验证证据用）
- kg_projection：section-local KG 的节点和边投影。projection 中的 unit_id 对应 section_text_with_unit_anchors 中同 ID 的原文块。原文块用于读取 unit 内容，projection 用于确认 KG 实际结构
- allowed_unit_ids

## 任务

对 S1 的每一个命题，逐个判断。**必须为每个命题输出恰好一条 boundary_decision。** candidate_id 必须使用 S1 给出的原始 ID（如 prop_001），不得自行生成新 ID。即使命题数量较多，也必须逐个处理，不得遗漏、不得合并、不得跳过。

- `p7c_candidate`：命题包含超出基础 KG 表达能力的局部程序性或判断性有向结构
- `kg_only`：命题已被基础 KG 充分表达

不构图，不创建节点和边，不选 node_type，不选 edge_type。

## KG 边界标准

基础 KG 已经能够充分表达：

- 定义、分类、事实和一般规则
- 普通例子或普通案例事实
- 孤立风险指标、红旗或控制措施
- 框架、产品、措施或标准的组成列表
- 一般概念关系、单纯主题相关性和普通机制因果
- CP 之间的包含、举例、铺垫、并列、对比和总结

以下结构可能属于 P7C 增量：

- 明确步骤、职责或交接顺序
- 条件、阈值或例外导向不同判断、分支或行动
- 事件、发现、结论或外部要求触发特定主体的应对
- 识别、评估、决策或执行动作产生与该动作语义独立的具体结论、记录、状态变化、控制结果或后续行动
- 线索或输入在特定判断中被采用，而不只是被列为风险指标
- 标准直接约束具体主体如何行动，或向机构制度、流程传导要求
- 结果触发复核、补充、更新、调优、监控或再次处理
- 案例中实际发生且未被基础 KG 充分表达的条件、决策、应对、交接或反馈链

单个 unit 可以成卡，只要其中完整存在上述增量结构。普通机制或原因导致后果仍由基础 KG 承接，只有它实际构成完整程序性或判断性有向结构的一部分时，才可进入 P7C。

基础 KG 能够把一条规则作为整体知识保存，不代表它已经表达了规则内部的条件、主体、动作、判断和结果之间的有向结构。遇到 `if/when/based on/must/should not/requires` 等规则时，检查其内部是否存在可支持选项判断的 P7C 增量结构。

结构复杂度不是成卡门槛。只要候选命题内部明确存在"情境/条件/标准/输入如何关联到特定主体的动作或判断"，即使它只有一个 unit、一条边、没有独立结果、没有分支或反馈，也判为 `p7c_candidate`。"规则简单""纯义务陈述""只是条件-动作链"不是跳过理由。

`kg_only` 只能表示基础 KG 已能表达候选的全部有效结构，例如纯定义、纯阈值事实、普通案例机制、孤立指标或一般知识关系；如果基础 KG 只能保存整句话，却不能表达句内的主体、方向、条件或动作结果关系，则仍属于 P7C 增量。

## 正反边界示例

以下属于 P7C 增量（p7c_candidate）：

- "机构必须遵守当地监管要求识别PEP"：有主体、动作和方向的约束关系，"纯义务"不是交给 KG 的理由
- "机构可根据风险偏好选择执行更高的PEP标准"：风险偏好条件导向机构可选的标准配置变化
- "如果银行知道或怀疑还贷资金非法，则不应接受"：条件 entry 导向具体应对动作
- "通常按25%识别UBO；高风险时阈值可能降至10%或5%"：阈值和例外条件导向差异化分类路径

以下通常只由基础 KG 承接（kg_only）：

- "调查环境犯罪可能受到被贿赂官员阻碍"：只有普通机制说明，没有完整的主体处置或判断结构
- "犯罪分子使用BMPE转换资金并掩饰来源"：普通案例机制，无条件、职责、判断或应对结构
- "某项措施维护合规诚信、降低风险"：只有抽象目的，没有证据支持的具体持续义务或独立结果

结构复杂度不是成卡门槛。只要命题明确了主体、动作和方向，即使只有一个 unit、没有独立结果，也判为 p7c_candidate。纯定义、纯阈值事实、普通案例机制、孤立风险指标才是 kg_only。

## 输出要求

**即使所有命题都是 kg_only，也必须为每个命题逐条输出 boundary_decision，不得输出空数组。** candidate_id 必须使用 S1 的原始 ID。

## 输出结构

```json
{
  "section_id": "<section_id>",
  "boundary_decisions": [
    {
      "candidate_id": "prop_001",
      "decision": "p7c_candidate",
      "reason": "<中文：为何超出 KG 表达能力>"
    },
    {
      "candidate_id": "prop_002",
      "decision": "kg_only",
      "reason": "<中文：为什么 KG 已能充分表达>"
    }
  ]
}
```

只输出 `boundary_decisions`，不输出 cards、coverage_audit、flow_nodes、flow_edges。

## 当前section

section_id: `CH08-S05`

section_title: `Private banking and wealth management risks > Special purpose vehicle risks`

kg_projection:

```json
{
  "kg_capability_profile": "base_kg_atomic_cp_v1",
  "units": [
    {
      "unit_id": "v7u_N000642",
      "type": "definition"
    },
    {
      "unit_id": "v7u_N000643",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000644",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000645",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000646",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000647",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000648",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000649",
      "type": "classification"
    },
    {
      "unit_id": "v7u_N000650",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000651",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000652",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000653",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000654",
      "type": "definition"
    },
    {
      "unit_id": "v7u_N000655",
      "type": "risk_indicator"
    },
    {
      "unit_id": "v7u_N000656",
      "type": "process"
    },
    {
      "unit_id": "v7u_N000657",
      "type": "fact"
    },
    {
      "unit_id": "v7u_N000658",
      "type": "rule"
    },
    {
      "unit_id": "v7u_N000659",
      "type": "rule"
    },
    {
      "unit_id": "v7u_N000660",
      "type": "fact"
    }
  ],
  "core_points": [
    {
      "core_point_id": "cp_CH08-S05_001",
      "title_zh": "SPV定义与合法用途",
      "title_en": "SPV Definition and Legitimate Uses"
    },
    {
      "core_point_id": "cp_CH08-S05_002",
      "title_zh": "SPV金融犯罪风险与红旗信号",
      "title_en": "SPV Financial Crime Risks and Red Flags"
    },
    {
      "core_point_id": "cp_CH08-S05_003",
      "title_zh": "集合投资工具（PIV）定义与风险",
      "title_en": "Pooled Investment Vehicle (PIV) Definition and Risks"
    },
    {
      "core_point_id": "cp_CH08-S05_004",
      "title_zh": "利用SPV和PIV的贸易洗钱",
      "title_en": "Trade-Based Money Laundering Using SPVs and PIVs"
    },
    {
      "core_point_id": "cp_CH08-S05_005",
      "title_zh": "强化尽职调查与客户尽职调查要求",
      "title_en": "Enhanced Due Diligence (EDD) and CDD Requirements"
    }
  ],
  "core_point_unit_edges": [
    {
      "source_id": "cp_CH08-S05_001",
      "target_id": "v7u_N000642",
      "relation_type": "defines"
    },
    {
      "source_id": "cp_CH08-S05_001",
      "target_id": "v7u_N000643",
      "relation_type": "illustrates"
    },
    {
      "source_id": "cp_CH08-S05_001",
      "target_id": "v7u_N000644",
      "relation_type": "illustrates"
    },
    {
      "source_id": "cp_CH08-S05_001",
      "target_id": "v7u_N000645",
      "relation_type": "illustrates"
    },
    {
      "source_id": "cp_CH08-S05_002",
      "target_id": "v7u_N000646",
      "relation_type": "states_consequence"
    },
    {
      "source_id": "cp_CH08-S05_002",
      "target_id": "v7u_N000647",
      "relation_type": "explains"
    },
    {
      "source_id": "cp_CH08-S05_002",
      "target_id": "v7u_N000648",
      "relation_type": "describes_process"
    },
    {
      "source_id": "cp_CH08-S05_002",
      "target_id": "v7u_N000649",
      "relation_type": "provides_context"
    },
    {
      "source_id": "cp_CH08-S05_002",
      "target_id": "v7u_N000650",
      "relation_type": "indicates_risk"
    },
    {
      "source_id": "cp_CH08-S05_002",
      "target_id": "v7u_N000651",
      "relation_type": "indicates_risk"
    },
    {
      "source_id": "cp_CH08-S05_002",
      "target_id": "v7u_N000652",
      "relation_type": "indicates_risk"
    },
    {
      "source_id": "cp_CH08-S05_002",
      "target_id": "v7u_N000653",
      "relation_type": "indicates_risk"
    },
    {
      "source_id": "cp_CH08-S05_003",
      "target_id": "v7u_N000654",
      "relation_type": "defines"
    },
    {
      "source_id": "cp_CH08-S05_003",
      "target_id": "v7u_N000655",
      "relation_type": "indicates_risk"
    },
    {
      "source_id": "cp_CH08-S05_004",
      "target_id": "v7u_N000656",
      "relation_type": "describes_process"
    },
    {
      "source_id": "cp_CH08-S05_004",
      "target_id": "v7u_N000657",
      "relation_type": "explains"
    },
    {
      "source_id": "cp_CH08-S05_005",
      "target_id": "v7u_N000658",
      "relation_type": "prescribes_measure"
    },
    {
      "source_id": "cp_CH08-S05_005",
      "target_id": "v7u_N000659",
      "relation_type": "prescribes_measure"
    },
    {
      "source_id": "cp_CH08-S05_005",
      "target_id": "v7u_N000660",
      "relation_type": "states_consequence"
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH08-S05_001",
      "target_id": "cp_CH08-S05_002",
      "relation_type": "contrasts"
    },
    {
      "source_id": "cp_CH08-S05_002",
      "target_id": "cp_CH08-S05_004",
      "relation_type": "prepares"
    },
    {
      "source_id": "cp_CH08-S05_003",
      "target_id": "cp_CH08-S05_004",
      "relation_type": "prepares"
    },
    {
      "source_id": "cp_CH08-S05_002",
      "target_id": "cp_CH08-S05_005",
      "relation_type": "prepares"
    },
    {
      "source_id": "cp_CH08-S05_003",
      "target_id": "cp_CH08-S05_005",
      "relation_type": "prepares"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000642|642] Special purpose vehicles (SPVs) are legal entities created for specific and limited purposes.
ZH: 特殊目的载体（SPV）是为特定有限目的设立的法律实体

[v7u_N000643|643] SPVs can be used in mergers and acquisitions, joint ventures, real estate projects, infrastructure development, and energy projects.
ZH: SPV可用于并购、合资、房地产、基础设施和能源项目

[v7u_N000644|644] SPVs can also be used to manage and protect intellectual property assets including trademarks and copyrights.
ZH: SPV可用于管理和保护知识产权资产

[v7u_N000645|645] SPVs are often used in complex financial transactions and investments such as securities and asset-backed financing.
ZH: SPV常用于复杂金融交易和资产支持融资

[v7u_N000646|646] There are financial crime risks associated with SPVs.
ZH: SPV存在金融犯罪风险

[v7u_N000647|647] SPVs can have complex and opaque structures to disguise the true beneficial ownership.
ZH: SPV可能通过复杂不透明的结构掩盖真实受益所有人

[v7u_N000648|648] SPVs might be used to obscure the source of illicit funds. Criminals layer illicit proceeds through a series of transactions via the SPVs, transferring funds to or from financial institutions. This creates a complex web of
ZH: 犯罪分子通过SPV进行一系列交易来分层非法收益，掩盖资金来源

[v7u_N000649|649] There are several red flags that indicate attempts to disguise illicit funds or conduct fraudulent activities using SPVs. These include:
ZH: 列举利用SPV掩饰非法资金或欺诈活动的红旗信号信号

[v7u_N000650|650] Complex ownership structures involving multiple layers of companies
ZH: 涉及多层公司的复杂所有权结构是红旗信号

[v7u_N000651|651] Lack of transparency
ZH: 缺乏透明度是红旗信号

[v7u_N000652|652] Unclear purpose of the SPV
ZH: SPV目的不明确是红旗信号

[v7u_N000653|653] Criminals might select jurisdictions that have lenient regulatory oversight or tax-friendly environments. This enables them to hide their financial activities and minimize tax liabilities.
ZH: 犯罪分子选择监管宽松或税收优惠的司法管辖区以隐藏活动和避税

[v7u_N000654|654] Pooled investment vehicles (PIVs) are small investments pooled together from a large group of investors.
ZH: 集合投资工具（PIV）是从大量投资者汇集的小额投资

[v7u_N000655|655] PIVs can be used in Ponzi schemes and insider trading.
ZH: PIV可能被用于庞氏骗局和内幕交易

[v7u_N000656|656] Additionally, criminals might engage in trade-based money laundering using SPVs and PIVs. Criminals manipulate trade transactions between SPVs and PIVs by deflating or inflating prices.
ZH: 犯罪分子利用SPV和PIV进行贸易洗钱，操纵交易价格

[v7u_N000657|657] This process enables the movement of illicit funds while disguising it as legitimate trade activity.
ZH: 该过程将非法资金伪装成合法贸易活动进行转移

[v7u_N000658|658] Financial institutions must be vigilant in conducting enhanced due diligence (EDD) on SPVs and PIVs. It is important to ensure these investments comply with CDD regulations such as the Financial Crime Enforcement Network's CDD rule.
ZH: 金融机构必须对SPV和PIV进行强化尽职调查，遵守客户尽职调查规则

[v7u_N000659|659] Financial institutions must identify ultimate beneficial owners and understand the true purpose of these entities.
ZH: 金融机构必须识别最终受益所有人并了解实体真实目的

[v7u_N000660|660] This will help mitigate any potential financial crime risks associated with SPVs.
ZH: 这有助于减轻与SPV相关的金融犯罪风险
```

allowed_unit_ids:

```json
[
  "v7u_N000642",
  "v7u_N000643",
  "v7u_N000644",
  "v7u_N000645",
  "v7u_N000646",
  "v7u_N000647",
  "v7u_N000648",
  "v7u_N000649",
  "v7u_N000650",
  "v7u_N000651",
  "v7u_N000652",
  "v7u_N000653",
  "v7u_N000654",
  "v7u_N000655",
  "v7u_N000656",
  "v7u_N000657",
  "v7u_N000658",
  "v7u_N000659",
  "v7u_N000660"
]
```

## S1 发现的命题

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000658",
      "v7u_N000659",
      "v7u_N000660"
    ],
    "proposition": "金融机构必须对SPV和PIV进行强化尽职调查，识别最终受益所有人并了解实体真实目的，以减轻相关金融犯罪风险。",
    "source_quotes": [
      "Financial institutions must be vigilant in conducting enhanced due diligence (EDD) on SPVs and PIVs. It is important to ensure these investments comply with CDD regulations such as the Financial Crime Enforcement Network's CDD rule.",
      "Financial institutions must identify ultimate beneficial owners and understand the true purpose of these entities.",
      "This will help mitigate any potential financial crime risks associated with SPVs."
    ],
    "relation_cues": [
      "must",
      "important",
      "help mitigate"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "对SPV和PIV进行强化尽职调查，识别最终受益所有人并了解实体真实目的",
      "outcomes_or_paths": [
        "减轻与SPV相关的金融犯罪风险"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000658",
        "quote": "Financial institutions must be vigilant in conducting enhanced due diligence (EDD) on SPVs and PIVs. It is important to ensure these investments comply with CDD regulations such as the Financial Crime Enforcement Network's CDD rule."
      },
      {
        "unit_id": "v7u_N000659",
        "quote": "Financial institutions must identify ultimate beneficial owners and understand the true purpose of these entities."
      },
      {
        "unit_id": "v7u_N000660",
        "quote": "This will help mitigate any potential financial crime risks associated with SPVs."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
