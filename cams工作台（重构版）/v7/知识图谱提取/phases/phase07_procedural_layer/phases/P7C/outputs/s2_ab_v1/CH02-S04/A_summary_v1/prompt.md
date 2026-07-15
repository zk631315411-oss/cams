# P7C KG Boundary Adjudication v1

## 角色

你是 P7C KG 边界裁决器。S1 已经发现候选有向命题。你的唯一任务是逐个判断每个命题是否超出基础 KG 的充分表达能力。

## 输入

- S1 发现的命题列表（含 candidate_id、unit_ids、proposition、relation_cues）
- section_text_with_unit_anchors（验证证据用）
- base_kg_section_summary（去重参考，不作为事实证据）
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

section_id: `CH02-S04`

section_title: `Types of financial crime > Case example: FullTechGlobal corruption scandal`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "FullTechGlobal 案中的英国反贿赂法域外效力与合规教训",
      "title_en": "UK Bribery Act Extraterritoriality and Compliance Lessons from FullTechGlobal Case",
      "covered_units": [
        {
          "unit_id": "v7u_N000135",
          "unit_type": "fact",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000136",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000137",
          "unit_type": "rule",
          "kg_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000141",
          "unit_type": "case",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000143",
          "unit_type": "fact",
          "kg_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000144",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000131",
          "unit_type": "fact",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000132",
          "unit_type": "case",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000133",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000134",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000138",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000139",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000140",
          "unit_type": "case",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000142",
          "unit_type": "fact",
          "kg_role": "explains"
        }
      ]
    }
  ],
  "covered_relations": []
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
