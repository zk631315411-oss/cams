# P7C KG Boundary Adjudication v1

## 角色

你是 P7C KG 边界裁决器。S1 已经发现候选有向命题。你的唯一任务是逐个判断每个命题是否超出基础 KG 的充分表达能力。

## 输入

- S1 发现的命题列表（含 candidate_id、unit_ids、proposition、relation_cues）
- section_text_with_unit_anchors（验证证据用）
- base_kg_section_summary（去重参考，不作为事实证据）
- allowed_unit_ids

## 任务

对 S1 的每一个命题，逐个判断。**必须为每个命题输出恰好一条 boundary_decision，不得遗漏、不得合并、不得跳过。** 即使命题数量较多，也必须逐个处理。

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

section_id: `CH05-S04`

section_title: `Financial crime risks in relation to other types of risks > Operational, legal, concentration, and reputational risks`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "主要风险类型：运营、法律、集中度、声誉",
      "title_en": "Key risk types: operational, legal, concentration, reputational",
      "covered_units": [
        {
          "unit_id": "v7u_N000369",
          "unit_type": "classification",
          "kg_role": "classifies"
        }
      ]
    },
    {
      "title_zh": "运营风险：定义与监管挑战",
      "title_en": "Operational risk: definition and regulatory challenges",
      "covered_units": [
        {
          "unit_id": "v7u_N000370",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000375",
          "unit_type": "definition",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000376",
          "unit_type": "process",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000377",
          "unit_type": "risk_indicator",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000378",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        }
      ]
    },
    {
      "title_zh": "法律风险：来源、后果及AFC保护",
      "title_en": "Legal risk: sources, consequences, and AFC protection",
      "covered_units": [
        {
          "unit_id": "v7u_N000371",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000379",
          "unit_type": "definition",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000381",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000380",
          "unit_type": "fact",
          "kg_role": "states_consequence"
        }
      ]
    },
    {
      "title_zh": "集中度风险：过度敞口、缓解与管理",
      "title_en": "Concentration risk: over-exposure, mitigation, and management",
      "covered_units": [
        {
          "unit_id": "v7u_N000372",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000382",
          "unit_type": "rule",
          "kg_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000384",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000385",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000383",
          "unit_type": "fact",
          "kg_role": "prescribes_measure"
        }
      ]
    },
    {
      "title_zh": "声誉风险：特征与信任因素",
      "title_en": "Reputational risk: characteristics and trust factor",
      "covered_units": [
        {
          "unit_id": "v7u_N000373",
          "unit_type": "definition",
          "kg_role": "defines"
        },
        {
          "unit_id": "v7u_N000386",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000387",
          "unit_type": "fact",
          "kg_role": "explains"
        },
        {
          "unit_id": "v7u_N000388",
          "unit_type": "fact",
          "kg_role": "explains"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "主要风险类型：运营、法律、集中度、声誉",
      "target_title": "运营风险：定义与监管挑战",
      "relation_type": "contains"
    },
    {
      "source_title": "主要风险类型：运营、法律、集中度、声誉",
      "target_title": "法律风险：来源、后果及AFC保护",
      "relation_type": "contains"
    },
    {
      "source_title": "主要风险类型：运营、法律、集中度、声誉",
      "target_title": "集中度风险：过度敞口、缓解与管理",
      "relation_type": "contains"
    },
    {
      "source_title": "主要风险类型：运营、法律、集中度、声誉",
      "target_title": "声誉风险：特征与信任因素",
      "relation_type": "contains"
    }
  ]
}
```

section_text_with_unit_anchors:

```text
[v7u_N000369|369] Key risks that organizations face include: Operational, legal, concentration, and reputational.
ZH: 组织面临的主要风险类型包括：运营风险、法律风险、集中度风险和声誉风险。

[v7u_N000370|370] Operational risk is direct or indirect loss of operations due to inadequate or failed internal processes, people, or systems, or as a result of external events.
ZH: 运营风险是因内部流程、人员、系统不完善或外部事件导致直接或间接损失的风险。

[v7u_N000371|371] Legal risk is the possibility that criminal penalties, lawsuits, or contracts that cannot be enforced might harm an organization.
ZH: 法律风险是指刑事处罚、诉讼或不可执行合同可能损害组织的可能性。

[v7u_N000372|372] Concentration risk stems from over-exposure to a single customer or group of related customers.
ZH: 集中度风险源于对单一客户或关联客户群体的过度敞口。

[v7u_N000373|373] Reputational risk comes when an institution known to have weak controls is then targeted by criminals or avoided by stakeholders who lose confidence in the institution.
ZH: 声誉风险是指机构因控制薄弱而被犯罪分子利用或利益相关者失去信心而回避的风险。

[v7u_N000374|374] Although these risks are usually managed by non-AFC risk management teams, understanding the correlation with financial crime risk is indispensable.
ZH: 尽管这些风险通常由非金融犯罪防控团队管理，但理解其与金融犯罪风险的关联至关重要。

[v7u_N000375|375] Operational risk is complex and includes an organization’s ability to maintain AFC controls in an evolving regulatory environment across multiple jurisdictions.
ZH: 运营风险复杂，包括组织在多个司法管辖区不断变化的监管环境中维持金融犯罪防控控制的能力。

[v7u_N000376|376] Typically, a global organization makes the policies of its home regulator its base standard. The organization will then adjust to each host country’s laws.
ZH: 全球组织通常以母国监管机构政策为基础标准，再根据东道国法律进行调整。

[v7u_N000377|377] Evolving regulations might become misaligned with current business models and controls.
ZH: 不断演变的法规可能与现有业务模式和控制措施产生错位。

[v7u_N000378|378] Compliance programs must continually be updated.
ZH: 合规计划必须持续更新。

[v7u_N000379|379] Legal risk stems from potential violation of regulations, laws, and ethical practices.
ZH: 法律风险源于可能违反法规、法律和道德实践。

[v7u_N000380|380] Governments might issue administrative penalties or fines. Third parties, such as customers who feel damaged, might file lawsuits.
ZH: 政府可能处以行政处罚或罚款，受损客户等第三方可能提起诉讼。

[v7u_N000381|381] Adequate AFC controls add protection from crime and inappropriate relationships.
ZH: 充分的金融犯罪防控措施可防范犯罪及不当关系

[v7u_N000382|382] Concentration risk can be reduced by AFC controls and strategic diversification.
ZH: 金融犯罪防控与战略多元化可降低集中度风险

[v7u_N000383|383] Customer due diligence, enabled by technology, helps manage exposure.
ZH: 借助技术的客户尽职调查有助于管理风险敞口

[v7u_N000384|384] Concentration could occur in borrowing, funding, purchasing, provision of key services, or any other business relationship.
ZH: 集中度可能出现在借贷、融资、采购、关键服务提供等业务关系中

[v7u_N000385|385] Risk could increase through actions by a customer, or external actions involving a customer.
ZH: 风险可能因客户行为或涉及客户的外部行为而增加

[v7u_N000386|386] Reputational risk is difficult to quantify.
ZH: 声誉风险难以量化

[v7u_N000387|387] Trust takes a long time to earn but can be lost quickly. A single news story—even fake news—can drive away customers and investors.
ZH: 信任建立缓慢但易丧失，一条新闻即可驱离客户与投资者

[v7u_N000388|388] Many organizations deserve their reputations, good or bad, based on their chosen business practices and ethics.
ZH: 组织的声誉源于其商业实践与道德选择
```

allowed_unit_ids:

```json
[
  "v7u_N000369",
  "v7u_N000370",
  "v7u_N000371",
  "v7u_N000372",
  "v7u_N000373",
  "v7u_N000374",
  "v7u_N000375",
  "v7u_N000376",
  "v7u_N000377",
  "v7u_N000378",
  "v7u_N000379",
  "v7u_N000380",
  "v7u_N000381",
  "v7u_N000382",
  "v7u_N000383",
  "v7u_N000384",
  "v7u_N000385",
  "v7u_N000386",
  "v7u_N000387",
  "v7u_N000388"
]
```
