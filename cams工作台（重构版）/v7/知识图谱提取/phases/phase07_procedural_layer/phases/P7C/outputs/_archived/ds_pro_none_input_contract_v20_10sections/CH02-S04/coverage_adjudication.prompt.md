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

original_json:

```json
{
  "section_id": "CH02-S04",
  "section_title": "Types of financial crime > Case example: FullTechGlobal corruption scandal",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N000131"
      ],
      "proposition": "Sophie是金融机构的AFC经理",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅人物背景介绍，无程序性或判断性有向结构，基础KG可保存为事实。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000132",
        "v7u_N000138",
        "v7u_N000139",
        "v7u_N000140"
      ],
      "proposition": "Sophie发现负面新闻触发初步调查，并识别出贿赂手段",
      "decision": "p7c_card",
      "card_id": "p7card_CH02-S04_001",
      "reason": "发现事件触发了主体的调查动作，调查产生识别结论，形成明确的有向链，超出基础KG能表达的独立事实。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000133"
      ],
      "proposition": "FullTechGlobal面临贿赂腐败指控",
      "decision": "kg_only",
      "card_id": null,
      "reason": "案例事实陈述，无主体动作或判断，基础KG可存储为事件。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000134"
      ],
      "proposition": "负面新闻引发对英国反贿赂法域外条款的关切",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅表达抽象关切，无明确主体动作或具体判断流程，基础KG可表达。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000135"
      ],
      "proposition": "英国反贿赂法是全球最严格的反腐败法之一",
      "decision": "kg_only",
      "card_id": null,
      "reason": "法律定义或特点描述，属于一般知识，基础KG承接。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N000136"
      ],
      "proposition": "英国反贿赂法适用于有英国关联的公司，母公司对子公司腐败负责",
      "decision": "kg_only",
      "card_id": null,
      "reason": "法律适用范围规则，属于一般知识关系，基础KG可保存。"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N000137"
      ],
      "proposition": "域外管辖意味着非英国企业的英国母公司可能被起诉",
      "decision": "kg_only",
      "card_id": null,
      "reason": "法律后果说明，无主体动作或判断，基础KG可表达。"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N000141"
      ],
      "proposition": "Sophie审计发现内控缺陷和监管不足",
      "decision": "p7c_card",
      "card_id": "p7card_CH02-S04_002",
      "reason": "审计动作明确产生内控缺陷的识别结论，构成有向程序链，基础KG不能表达该生产关系。"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N000142"
      ],
      "proposition": "贿赂作为上游犯罪导致洗钱",
      "decision": "kg_only",
      "card_id": null,
      "reason": "犯罪机制解释，属于普通案例机制，基础KG承接。"
    },
    {
      "candidate_id": "cand_010",
      "unit_ids": [
        "v7u_N000143"
      ],
      "proposition": "FullTechGlobal面临严厉处罚、监管审查和刑事责任",
      "decision": "kg_only",
      "card_id": null,
      "reason": "案件后果描述，无主体判断或应对动作，基础KG可存储。"
    },
    {
      "candidate_id": "cand_011",
      "unit_ids": [
        "v7u_N000144"
      ],
      "proposition": "Sophie认识到机构需要维护合规诚信并降低贿赂风险",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般性认识或义务认知，未形成带明确主体现流程的有向结构，基础KG可表达。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH02-S04_001",
      "section_id": "CH02-S04",
      "card_nature": "execution",
      "title": "发现负面新闻触发初步调查并识别贿赂手段",
      "flow_nodes": [
        {
          "node_id": "E1_news_discovery",
          "node_category": "entry",
          "node_type": "E1_event_signal",
          "label": "Sophie发现客户FullTechGlobal Services的负面新闻",
          "evidence_unit_ids": [
            "v7u_N000132"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P2_initial_investigation",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "Sophie进行初步调查",
          "evidence_unit_ids": [
            "v7u_N000138"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X1_bribery_methods",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "识别到贿赂手段：利用中间人获取合同、虚增咨询费、伪造发票、使用壳公司、提供豪华礼品和旅行安排以影响决策",
          "evidence_unit_ids": [
            "v7u_N000138",
            "v7u_N000139",
            "v7u_N000140"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "edge_001",
          "edge_type": "PRECEDES",
          "source": "E1_news_discovery",
          "target": "P2_initial_investigation",
          "evidence_unit_ids": [
            "v7u_N000132",
            "v7u_N000138"
          ],
          "derivation": "llm_inference",
          "condition": "发现负面新闻后",
          "source_quote": "she came across negative news concerning their customer FullTechGlobal Services"
        },
        {
          "edge_id": "edge_002",
          "edge_type": "PRODUCES",
          "source": "P2_initial_investigation",
          "target": "X1_bribery_methods",
          "evidence_unit_ids": [
            "v7u_N000138",
            "v7u_N000139",
            "v7u_N000140"
          ],
          "derivation": "explicit_text",
          "relation_type": "identification_leads_to_conclusion",
          "source_quote": "initial investigation revealed that FullTechGlobal had strategically employed intermediaries... it appeared the subsidiary was systematically obscuring... evidence suggested that FullTechGlobal provided sophisticated inducements..."
        }
      ],
      "source_unit_ids": [
        "v7u_N000132",
        "v7u_N000138",
        "v7u_N000139",
        "v7u_N000140"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：发现负面新闻（事件）→初步调查（过程）→识别贿赂手段（结论）；KG不足：基础KG可将各单元作为独立事实存储，但不能表达事件触发调查及调查产生识别结论的有向关系；选项判断：可确认事件触发的顺序和调查产生的具体识别结果；LLM推理：edge_001为llm_inference，因原文未直述发现新闻直接导致调查，但根据时间顺序和AFC经理职责，是完成原文明示调查行为的必要前提，无其他合理解释。"
    },
    {
      "card_id": "p7card_CH02-S04_002",
      "section_id": "CH02-S04",
      "card_nature": "execution",
      "title": "审计发现内控缺陷和监管不足",
      "flow_nodes": [
        {
          "node_id": "P2_audit_review",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "Sophie跟进调查并开展审计",
          "evidence_unit_ids": [
            "v7u_N000141"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X1_control_deficiencies",
          "node_category": "exit",
          "node_type": "X1_classification",
          "label": "发现FullTechGlobal的ABC框架和内控失灵，包括内部监控机制缺陷和监督不足，助长了长期未被发现的腐败活动",
          "evidence_unit_ids": [
            "v7u_N000141"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "edge_003",
          "edge_type": "PRODUCES",
          "source": "P2_audit_review",
          "target": "X1_control_deficiencies",
          "evidence_unit_ids": [
            "v7u_N000141"
          ],
          "derivation": "explicit_text",
          "relation_type": "identification_leads_to_conclusion",
          "source_quote": "She followed up on the investigation and conducted a review that identified failures within FullTechGlobal’s ABC framework and internal controls. Her audit uncovered deficiencies in internal control mechanisms and inadequate oversight, which facilitated prolonged and undetected corrupt activities."
        }
      ],
      "source_unit_ids": [
        "v7u_N000141"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：审计过程→识别内控缺陷和监管不足（结论）；KG不足：基础KG可将审计及缺陷作为事实存储，但不能表达审计产生该识别结论的有向过程；选项判断：可确认审计动作是否导致特定内控缺陷的识别；LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```

review_target_candidate_ids:

```json
[
  "cand_001",
  "cand_003",
  "cand_004",
  "cand_005",
  "cand_006",
  "cand_007",
  "cand_009",
  "cand_010",
  "cand_011"
]
```
