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

section_id: `CH06-S09`

section_title: `Money Laundering Risks in Financial Services > Politically exposed person risks`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "政治敏感人物的定义、范围和关联人",
      "title_en": "PEP definition, scope, and related persons",
      "covered_units": [
        {
          "unit_id": "v7u_N000457",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000469",
          "unit_type": "fact",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000470",
          "unit_type": "fact",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000473",
          "unit_type": "fact",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000474",
          "unit_type": "fact",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000475",
          "unit_type": "fact",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000467",
          "unit_type": "rule",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000468",
          "unit_type": "classification",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000471",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000472",
          "unit_type": "classification",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "政治敏感人物识别挑战与合规要求",
      "title_en": "PEP Identification Challenges and Compliance",
      "covered_units": [
        {
          "unit_id": "v7u_N000458",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000459",
          "unit_type": "rule",
          "kg_role": "states_rule"
        },
        {
          "unit_id": "v7u_N000460",
          "unit_type": "rule",
          "kg_role": "explains"
        }
      ]
    },
    {
      "title_zh": "FATF对政治敏感人物的分类",
      "title_en": "FATF Classification of PEP Types",
      "covered_units": [
        {
          "unit_id": "v7u_N000462",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N000463",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N000464",
          "unit_type": "fact",
          "kg_role": "classifies"
        },
        {
          "unit_id": "v7u_N000461",
          "unit_type": "classification",
          "kg_role": "provides_context"
        }
      ]
    },
    {
      "title_zh": "政治敏感人物的腐败风险与示例",
      "title_en": "PEP Vulnerability to Corruption and Examples",
      "covered_units": [
        {
          "unit_id": "v7u_N000465",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000466",
          "unit_type": "case",
          "kg_role": "illustrates"
        }
      ]
    },
    {
      "title_zh": "政治敏感人物风险管理与监控方法",
      "title_en": "PEP Risk Management and Monitoring Approaches",
      "covered_units": [
        {
          "unit_id": "v7u_N000476",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000477",
          "unit_type": "rule",
          "kg_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000481",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000482",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000479",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000478",
          "unit_type": "classification",
          "kg_role": "provides_context"
        },
        {
          "unit_id": "v7u_N000480",
          "unit_type": "rule",
          "kg_role": "explains"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "政治敏感人物的定义、范围和关联人",
      "target_title": "FATF对政治敏感人物的分类",
      "relation_type": "prepares"
    },
    {
      "source_title": "政治敏感人物的定义、范围和关联人",
      "target_title": "政治敏感人物的腐败风险与示例",
      "relation_type": "prepares"
    },
    {
      "source_title": "政治敏感人物的定义、范围和关联人",
      "target_title": "政治敏感人物风险管理与监控方法",
      "relation_type": "prepares"
    },
    {
      "source_title": "政治敏感人物识别挑战与合规要求",
      "target_title": "政治敏感人物风险管理与监控方法",
      "relation_type": "prepares"
    },
    {
      "source_title": "FATF对政治敏感人物的分类",
      "target_title": "政治敏感人物的腐败风险与示例",
      "relation_type": "prepares"
    },
    {
      "source_title": "政治敏感人物的腐败风险与示例",
      "target_title": "政治敏感人物风险管理与监控方法",
      "relation_type": "prepares"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000457|457] A politically exposed person (PEP) is an individual in a prominent political function, their immediate family, close associates, and any businesses held or controlled by that person.
ZH: 政治敏感人物（政治敏感人物）的定义：担任重要公职的个人及其亲属和密切关联人

[v7u_N000458|458] One challenge in identifying PEPs is the varying guidance and recommendations in each jurisdiction.
ZH: 识别政治敏感人物的挑战在于各司法管辖区指引不同

[v7u_N000459|459] Organizations must adhere to their local regulatory requirements in identifying PEPs.
ZH: 机构必须遵守当地监管要求识别政治敏感人物

[v7u_N000460|460] However, organizations may choose to enforce higher standards based on their risk appetite.
ZH: 机构可根据风险偏好执行更高的政治敏感人物标准

[v7u_N000461|461] According to the Financial Action Task Force (FATF), there are three types of PEPs:
ZH: FATF将政治敏感人物分为三类

[v7u_N000462|462] Foreign PEPs are individuals entrusted with prominent public functions by a foreign country.
ZH: 外国政治敏感人物指受外国委托担任重要公共职能的个人

[v7u_N000463|463] Domestic PEPs are individuals entrusted domestically with prominent public functions.
ZH: 国内政治敏感人物指在国内担任重要公共职能的个人

[v7u_N000464|464] International organization PEPs are individuals from an international organization entrusted with a prominent function such as secretary general, executive director, or president.
ZH: 国际组织政治敏感人物指在国际组织中担任秘书长、执行董事或主席等要职的个人

[v7u_N000465|465] Individuals in high positions and their associates are more vulnerable to corruption.
ZH: 高层职位个人及其关联人更易受腐败影响

[v7u_N000466|466] Corruption might be favors where the PEP directs government contracts to an organization in return for kickbacks. In addition, a PEP might influence legislation for bribes or flee the country with government funds.
ZH: 政治敏感人物腐败示例：以政府合同换取回扣、影响立法收受贿赂或携政府资金潜逃

[v7u_N000467|467] Use a broad definition for defining a PEP.
ZH: 应采用宽泛定义来界定政治敏感人物

[v7u_N000468|468] PEPs can generally be defined as:
ZH: 政治敏感人物的一般定义

[v7u_N000469|469] A person in a prominent decision-making or influential role
ZH: 政治敏感人物指担任重要决策或有影响力角色的人

[v7u_N000470|470] A person within royal, military, legislative, judicial, executive, or similar government positions
ZH: 政治敏感人物包括王室、军事、立法、司法、行政或类似政府职位的人

[v7u_N000471|471] PEPs will often use nominees or businesses they are associated with.
ZH: 政治敏感人物常使用名义人或关联企业

[v7u_N000472|472] Therefore, the definition of PEP can also include:
ZH: 政治敏感人物定义还可包括以下人员

[v7u_N000473|473] Immediate family
ZH: 政治敏感人物的直系亲属

[v7u_N000474|474] Close friends or associates
ZH: 政治敏感人物的密友或关联人

[v7u_N000475|475] Businesses owned or held by those individuals
ZH: 政治敏感人物拥有或持有的企业

[v7u_N000476|476] Under a risk-based approach, PEP risk is manageable.
ZH: 基于风险的方法下，政治敏感人物风险是可控的

[v7u_N000477|477] Some organizations follow a “once a PEP, always a PEP” approach because the individual may remain in the same circles of influence, even if they have stepped down.
ZH: 部分机构采用“一旦是政治敏感人物，永远是政治敏感人物”的方法

[v7u_N000478|478] Other organizations will look at:
ZH: 其他机构会考察以下因素

[v7u_N000479|479] The individual’s influence at the time, such as their ability to award contracts or allocate funds
ZH: 考察个人当时的影响力，如授予合同或分配资金的能力

[v7u_N000480|480] How long the individual has been classified as a PEP
ZH: 考察个人被归类为政治敏感人物的时间长短

[v7u_N000481|481] The purpose of the PEP designation is important.
ZH: 政治敏感人物 认定的目的具有重要意义

[v7u_N000482|482] Organizations must take the necessary steps to adapt transaction monitoring and KYC reviews and escalate based on their risk appetite.
ZH: 机构必须根据风险偏好调整交易监控和 了解你的客户 审查
```

allowed_unit_ids:

```json
[
  "v7u_N000457",
  "v7u_N000458",
  "v7u_N000459",
  "v7u_N000460",
  "v7u_N000461",
  "v7u_N000462",
  "v7u_N000463",
  "v7u_N000464",
  "v7u_N000465",
  "v7u_N000466",
  "v7u_N000467",
  "v7u_N000468",
  "v7u_N000469",
  "v7u_N000470",
  "v7u_N000471",
  "v7u_N000472",
  "v7u_N000473",
  "v7u_N000474",
  "v7u_N000475",
  "v7u_N000476",
  "v7u_N000477",
  "v7u_N000478",
  "v7u_N000479",
  "v7u_N000480",
  "v7u_N000481",
  "v7u_N000482"
]
```
