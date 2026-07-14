# P7C Section-Local Coverage Adjudication Prompt v2

## 角色

你是P7C覆盖裁决器。首次抽取器已经发现候选命题并生成候选card；这些card尚未经过P7D正式结构校验和边级审核。你的唯一任务是复核`coverage_audit`中原决定为`kg_only`的候选，判断它们是否因KG/P7C边界理解错误而漏成卡。

只输出严格JSON补丁，不输出Markdown或解释。`original_json`提供本次无记忆API调用所需的完整首次抽取上下文；不得回显或改写它。Runner会把补丁确定性合并到P7C正本。

## P7C目的

P7C在不重复基础KG已经能够充分表达的定义、分类、事实、普通案例、孤立风险指标和一般知识关系的前提下，从单个section中增量提取对CAMS题目选项判断有用的局部程序性或判断性有向结构：业务情境、事件、线索、输入或标准如何关联到特定主体带原文情态的识别、评估、决策或应对，以及原文明示的独立结论、记录、状态变化、控制效果、分支或后续行动。没有独立结果时允许开放关系。

P7C不读取题目或参考答案，不处理跨section桥接。当前section原文是唯一事实证据；基础KG摘要只能用于去重，不能补造事实。

## 裁决对象

只复核`original_json.coverage_audit`中`decision=kg_only`的候选。不得新增候选，不得删除候选，不得修改候选的`candidate_id`、`unit_ids`或`proposition`。

原本为`p7c_card`的候选及`original_json.cards`只用于理解已有结果、避免重复和避开已占用ID。输出中不得包含、删除、改写、拆分、合并或重新编号这些既有内容。

## 裁决标准

将原`kg_only`候选提升为`p7c_card`，必须同时满足：

1. 当前section证据支持关系两端、特定主体、方向以及条件（如有）。
2. 候选内部存在“情境/事件/线索/输入/标准如何关联到主体动作或判断”的局部结构；只有原文明示独立结果时才增加结果节点。
3. 该方向结构能够帮助判断选项的顺序、条件、主体职责、义务、应对、因果或适用范围。
4. 基础KG只能保存整句话或各知识点，不能充分表达句内的主体、方向、条件、动作约束或独立结果关系。

结构复杂度和是否闭环不是门槛。一个unit、一条路径、没有分支或反馈，或没有独立出口，都不能作为`kg_only`理由。只有对象实际到达、提交、移交或进入某阶段并触发动作时才建entry；静态适用对象、线索输入、分析材料、风险阈值、监管要求、政策基准或风险偏好应作为auxiliary standard/input并由process通过`REFERENCES`指向。

不得用“纯义务陈述”“没有复杂条件”“没有复杂步骤”拒绝提升。只要候选已经明确给出监管要求、风险偏好或状态变化如何约束特定主体的识别、标准选择或分类维持，即使没有独立出口，也满足局部有向结构要求。

以下通常应提升：

- 金融机构的识别动作明确参照监控系统标记的异常活动；只有原文另行给出识别结论时才增加出口。
- FIU综合SAR和跨境活动并形成红旗发现。
- 风险阈值和直接/间接持股被机构用于UBO判断并形成分类结论。
- 外部监管要求或上位标准约束机构调整控制、政策或职责；除非原文明示命令到达后触发动作，否则使用`REFERENCES`而不是`PRECEDES`。
- 明确条件触发拒绝、批准、升级、报告、监控或复核。
- 当地监管要求约束机构如何识别PEP；不得因规则只有一个unit或没有义务出口而拒绝。
- 机构基于风险偏好可以选择更高标准；必须保留可选性，即使没有独立配置出口也可以作为开放式局部关系。
- 卸任等状态变化后，特定机构仍明确维持既有分类；必须保留“部分机构”“可能”等限定。

以下保持`kg_only`：

- 纯定义、分类、阈值数值或组成列表，没有主体应用或其他有向关系。
- 普通犯罪方法、犯罪分子操作步骤或普通案例机制，没有机构、FIU、监管或执法主体的识别、判断或应对。
- 孤立红旗、后果、历史事实或抽象风险缓解目的。
- 只有主题相关性，或者必须补造主体、条件、方向、动作或结果才能闭合。

## 修改规则

对`review_target_candidate_ids`中的每个原`kg_only`候选，在顶层`coverage_adjudication`中输出一条记录：

```json
{
  "candidate_id": "cand_001",
  "original_decision": "kg_only",
  "final_decision": "kg_only",
  "card_id": null,
  "reason": "<中文裁决理由>"
}
```

`final_decision`只能为`kg_only`或`p7c_card`。

保持`kg_only`时：`card_id`必须为`null`。

提升为`p7c_card`时：

- 在裁决记录中填写新card的`card_id`；
- `reason`说明基础KG不能表达的方向结构；
- 在顶层`promoted_cards`中输出且只输出对应的新card；
- 新card ID不得与`original_json.cards`中的既有ID重复；
- 每个提升候选恰好对应一张新card，不得输出未被裁决提升的card。

## 新增card规则

新增card必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, candidate_status, review_notes`。`candidate_status`固定为`candidate`，不是最终审核状态。

`card_nature`只能为：`execution, assessment, risk_indicator, control`。

新增card可以是完整闭环，也可以是开放式局部关系；不得为了满足entry→process→exit而补造出口。

节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。节点必须由原文明示，`evidence_strength`只能为`explicit`。

允许节点类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

`X7_continuing_obligation`只用于原文明示上游动作、决定或协议新建立了独立持续义务；规范性语句中的“主体必须/应当执行某动作”应保留在process中，不得复制为X7出口。

边必填：`edge_id, edge_type, source, target, evidence_unit_ids, derivation`。允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

- `REFERENCES`只能由process指向auxiliary input或standard。
- `PRODUCES`只能由process指向exit。
- `DECIDES`只能由`P3_branch_routing`发出，至少两条分支，每条都有原文明示的`condition`。
- `derivation=llm_inference`只说明边依赖必要功能推理，不改变`candidate_status`，也不表示P7D已经接受或拒绝。

`REFERENCES.condition`可以限定某项input/standard适用于process的情境，但不表示条件分支。单一条件直接触发动作时使用带`condition`的`PRECEDES`；只有至少两条原文明示路径时才使用`DECIDES`。

静态适用对象、审查材料或判断输入不得仅因语法顺序建成`entry --PRECEDES--> process`；应建为auxiliary input并由process通过`REFERENCES`指向。不得把同一谓词的主动式和被动式拆成process与exit，也不得把“动作需要理由、批准或遵循要求”写成“动作`PRODUCES`要求/义务”。

单一路径的`if/when/unless A，则B`使用条件entry到process的`PRECEDES`，并在edge的`condition`中保留原文条件；它表达逻辑前提，不要求钟表式先后。输出每条`PRODUCES`前必须反问：source和target合并后是否仍损失一个独立事实；若不损失，删除同义target和该边。理由、批准、标准或义务约束动作时使用process指向standard/input的`REFERENCES`。

默认省略`relation_type`。只有完全符合允许语义和端点约束时才填写，不得创造新类型。

必须保留`must, should, may, might, could, often, potentially, help`等情态强度。不得将“有助于缓解”强化为“风险已经消除”。`must/shall/is required to`只证明义务存在，不证明动作已经完成；除非原文明示完成或结果已经发生，不得输出“已调整”“已建立”“已降低”等完成状态。

`must`本身不证明义务是持续、定期、永久或反复的，不得无证据增加这些限定。`escalate/escalation`默认写成“升级处理/升级处置”或保留英文，不得翻译为“上报/报告”；只有原文明示`report/notify/file/refer`及其对象时，才能写成上报、报告或移交。

新增card的节点、边和`source_unit_ids`只能引用对应候选原有的`unit_ids`。不得借裁决轮追加其他unit、扩展候选命题或引入无关主题；若原候选证据本身不足，保持`kg_only`。

## 输出约束

只返回补丁对象，顶层只能包含：

```text
section_id
coverage_adjudication
promoted_cards
```

示例：

```json
{
  "section_id": "<section_id>",
  "coverage_adjudication": [
    {
      "candidate_id": "cand_001",
      "original_decision": "kg_only",
      "final_decision": "kg_only",
      "card_id": null,
      "reason": "<中文KG边界理由>"
    }
  ],
  "promoted_cards": []
}
```

即使所有候选都保持`kg_only`，也必须逐一输出裁决记录，此时`promoted_cards`为空数组。不得输出`coverage_audit`、既有`cards`、`skip_reason`或其他首次抽取字段。

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

original_json:

```json
{
  "section_id": "CH05-S04",
  "section_title": "Financial crime risks in relation to other types of risks > Operational, legal, concentration, and reputational risks",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N000376"
      ],
      "proposition": "全球组织通常以母国监管政策为基础标准，并根据东道国法律调整合规政策",
      "decision": "p7c_card",
      "card_id": "p7card_CH05-S04_001",
      "reason": "基础KG不能表达调整动作与监管标准之间的有向约束关系，此结构可帮助选项判断主体如何根据标准调整合规政策。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000369"
      ],
      "proposition": "风险类型列表：运营、法律、集中度、声誉",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯粹的分类列表，基础KG可表达。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000370",
        "v7u_N000375"
      ],
      "proposition": "运营风险定义及其复杂性，包括维持AFC控制的能力",
      "decision": "kg_only",
      "card_id": null,
      "reason": "定义和一般说明，无局部程序性或判断性有向结构。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000377"
      ],
      "proposition": "不断演变的法规可能与现有业务模式和控制措施产生错位",
      "decision": "kg_only",
      "card_id": null,
      "reason": "孤立的风险指标，基础KG可表达。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000378"
      ],
      "proposition": "合规计划必须持续更新",
      "decision": "kg_only",
      "card_id": null,
      "reason": "纯义务陈述，基础KG可作为规则保存。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N000371",
        "v7u_N000379",
        "v7u_N000380",
        "v7u_N000381"
      ],
      "proposition": "法律风险来源、可能后果（行政处罚、诉讼）及AFC控制的保护作用",
      "decision": "kg_only",
      "card_id": null,
      "reason": "定义、一般后果和一般保护关系，基础KG可充分表达。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N000372",
        "v7u_N000382",
        "v7u_N000383",
        "v7u_N000384",
        "v7u_N000385"
      ],
      "proposition": "集中度风险定义、出现领域、增加因素及控制措施（AFC、技术CDD）的一般效果",
      "decision": "kg_only",
      "card_id": null,
      "reason": "定义、事实和一般风险缓解关系，基础KG可表达。"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N000373",
        "v7u_N000386",
        "v7u_N000387",
        "v7u_N000388"
      ],
      "proposition": "声誉风险特征、难以量化、信任易失和基于实践的特点",
      "decision": "kg_only",
      "card_id": null,
      "reason": "特征描述和事实，无程序性结构。"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N000374"
      ],
      "proposition": "理解金融犯罪风险与其他风险的关联至关重要",
      "decision": "kg_only",
      "card_id": null,
      "reason": "抽象重要性陈述，无具体动作或判断。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH05-S04_001",
      "section_id": "CH05-S04",
      "card_nature": "execution",
      "title": "全球组织根据母国政策和东道国法律调整合规政策",
      "flow_nodes": [
        {
          "node_id": "P1",
          "node_category": "process",
          "node_type": "P8_constrained_action",
          "label": "全球组织通常以母国监管政策为基础标准，并根据东道国法律调整合规政策",
          "evidence_unit_ids": [
            "v7u_N000376"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "S1",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "母国监管机构政策",
          "evidence_unit_ids": [
            "v7u_N000376"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "S2",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "各东道国法律",
          "evidence_unit_ids": [
            "v7u_N000376"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "E1",
          "edge_type": "REFERENCES",
          "source": "P1",
          "target": "S1",
          "evidence_unit_ids": [
            "v7u_N000376"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        },
        {
          "edge_id": "E2",
          "edge_type": "REFERENCES",
          "source": "P1",
          "target": "S2",
          "evidence_unit_ids": [
            "v7u_N000376"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action"
        }
      ],
      "source_unit_ids": [
        "v7u_N000376"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：全球组织通常调整合规政策 --REFERENCES--> 母国监管政策及东道国法律；KG不足：基础KG不能表达调整动作受标准约束的有向关系；选项判断：可确认或排除关于组织如何根据监管环境调整政策的选项；LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```

review_target_candidate_ids:

```json
[
  "cand_002",
  "cand_003",
  "cand_004",
  "cand_005",
  "cand_006",
  "cand_007",
  "cand_008",
  "cand_009"
]
```
