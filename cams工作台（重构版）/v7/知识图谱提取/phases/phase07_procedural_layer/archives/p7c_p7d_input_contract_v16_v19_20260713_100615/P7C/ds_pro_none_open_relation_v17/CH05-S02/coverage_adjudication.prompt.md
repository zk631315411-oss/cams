# P7C Section-Local Coverage Adjudication Prompt v1

## 角色

你是P7C覆盖裁决器。首次抽取器已经发现候选命题并生成通过结构校验的card；你的唯一任务是复核`coverage_audit`中原决定为`kg_only`的候选，判断它们是否因KG/P7C边界理解错误而漏成卡。

只输出完整严格JSON，不输出Markdown或解释。`flow_nodes + flow_edges`仍是知识正本；`coverage_adjudication`和`coverage_audit`只是诊断元数据。

## P7C目的

P7C在不重复基础KG已经能够充分表达的定义、分类、事实、普通案例、孤立风险指标和一般知识关系的前提下，从单个section中增量提取对CAMS题目选项判断有用的局部程序性或判断性有向结构：业务情境、事件、线索、输入或标准，如何关联到特定主体的识别、评估、决策或应对，并在相应条件下产生结论、义务、控制结果、分支或后续行动。

P7C不读取题目或参考答案，不处理跨section桥接。当前section原文是唯一事实证据；基础KG摘要只能用于去重，不能补造事实。

## 裁决对象

只复核`original_json.coverage_audit`中`decision=kg_only`的候选。不得新增候选，不得删除候选，不得修改候选的`candidate_id`、`unit_ids`或`proposition`。

原本为`p7c_card`的候选及其`card_id`必须保持不变。`original_json.cards`中的每张既有card必须完整保留，不得删除、改写、拆分、合并或重新编号。

## 裁决标准

将原`kg_only`候选提升为`p7c_card`，必须同时满足：

1. 当前section证据支持关系两端、特定主体、方向以及条件（如有）。
2. 候选内部存在“情境/事件/线索/输入/标准如何关联到主体动作或判断”的局部结构；只有原文明示独立结果时才增加结果节点。
3. 该方向结构能够帮助判断选项的顺序、条件、主体职责、义务、应对、因果或适用范围。
4. 基础KG只能保存整句话或各知识点，不能充分表达句内的主体、方向、条件及动作结果关系。

结构复杂度和是否闭环不是门槛。一个unit、一条路径、没有分支或反馈，或没有独立出口，都不能作为`kg_only`理由。只有对象实际到达、提交、移交或进入某阶段并触发动作时才建entry；静态适用对象、线索输入、分析材料、风险阈值、监管要求、政策基准或风险偏好应作为auxiliary standard/input并由process通过`REFERENCES`指向。

不得用“纯义务陈述”“没有复杂条件”“没有复杂步骤”拒绝提升。只要候选已经明确给出监管要求、风险偏好或状态变化如何约束特定主体的识别、标准选择或分类维持，即使没有独立出口，也满足局部有向结构要求。

以下通常应提升：

- 金融机构监控系统根据异常活动进行标记并形成识别结论。
- FIU综合SAR和跨境活动并形成红旗发现。
- 风险阈值和直接/间接持股被机构用于UBO判断并形成分类结论。
- 外部监管要求或上位标准约束机构调整控制、政策或职责；除非原文明示命令到达后触发动作，否则使用`REFERENCES`而不是`PRECEDES`。
- 明确条件触发拒绝、批准、升级、报告、监控或复核。
- 当地监管要求约束机构如何识别PEP；不得因规则只有一个unit或没有义务出口而拒绝。
- 机构基于风险偏好可以选择更高标准；必须保留可选性，即使没有独立配置出口也可以作为开放式局部关系。
- 卸任等状态变化后，特定机构仍明确维持既有分类；必须保留“部分机构”“可能”等限定。

以下保持`kg_only`：

- 纯定义、分类、阈值数值或组成列表，没有主体应用和结果关系。
- 普通犯罪方法、犯罪分子操作步骤或普通案例机制，没有机构、FIU、监管或执法主体的识别、判断或应对。
- 孤立红旗、后果、历史事实或抽象风险缓解目的。
- 只有主题相关性，或者必须补造主体、条件、方向、动作或结果才能闭合。

## 修改规则

对每个原`kg_only`候选，在顶层`coverage_adjudication`中新增一条记录：

```json
{
  "candidate_id": "cand_001",
  "original_decision": "kg_only",
  "final_decision": "kg_only",
  "reason": "<中文裁决理由>"
}
```

`final_decision`只能为`kg_only`或`p7c_card`。

保持`kg_only`时：原`coverage_audit`记录的`decision`仍为`kg_only`，`card_id`仍为`null`，可以更新中文`reason`。

提升为`p7c_card`时：

- 将原`coverage_audit`记录的`decision`改为`p7c_card`；
- 填入新增card的`card_id`；
- 更新中文`reason`，说明基础KG不能表达的方向结构；
- 在`cards`末尾追加一张有证据的局部card；
- 不得修改其他候选或已有card。

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

边必填：`edge_id, edge_type, source, target, evidence_unit_ids, derivation`。允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

- `REFERENCES`只能由process指向auxiliary input或standard。
- `PRODUCES`只能由process指向exit。
- `DECIDES`只能由`P3_branch_routing`发出，至少两条分支，每条都有原文明示的`condition`。
- `derivation=llm_inference`只说明边依赖必要功能推理，不改变`candidate_status`，也不表示P7D已经接受或拒绝。

静态适用对象、审查材料或判断输入不得仅因语法顺序建成`entry --PRECEDES--> process`；应建为auxiliary input并由process通过`REFERENCES`指向。不得把同一谓词的主动式和被动式拆成process与exit，也不得把“动作需要理由、批准或遵循要求”写成“动作`PRODUCES`要求/义务”。

默认省略`relation_type`。只有完全符合允许语义和端点约束时才填写，不得创造新类型。

必须保留`must, should, may, might, could, often, potentially, help`等情态强度。不得将“有助于缓解”强化为“风险已经消除”。`must/shall/is required to`只证明义务存在，不证明动作已经完成；除非原文明示完成或结果已经发生，不得输出“已调整”“已建立”“已降低”等完成状态。

`must`本身不证明义务是持续、定期、永久或反复的，不得无证据增加这些限定。`escalate/escalation`默认写成“升级处理/升级处置”或保留英文，不得翻译为“上报/报告”；只有原文明示`report/notify/file/refer`及其对象时，才能写成上报、报告或移交。

新增card只能引用对应候选`unit_ids`及同一局部命题必要的当前section unit。不得借裁决轮扩展到无关主题。

## 输出约束

返回完整顶层对象：

```text
section_id
section_title
coverage_adjudication
coverage_audit
cards
skip_reason
```

如果最终存在card，`skip_reason`必须为`null`。如果仍无card，保留合适的中文`skip_reason`。

## 当前section

section_id: `CH05-S02`

section_title: `Financial crime risks in relation to other types of risks > Case example: A lasting lesson`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH05_S02_001",
      "title_zh": "汇丰案例教训：薄弱的金融犯罪控制导致严厉处罚、运营中断和持久声誉损害",
      "title_en": "HSBC case lesson: weak financial crime controls lead to severe penalties, operational disruption, and lasting reputational damage",
      "anchor_unit_ids": [
        "v7u_N000363"
      ],
      "key_unit_ids": [
        "v7u_N000363",
        "v7u_N000360",
        "v7u_N000362",
        "v7u_N000356",
        "v7u_N000357"
      ],
      "support_unit_ids": [
        "v7u_N000356",
        "v7u_N000357",
        "v7u_N000358",
        "v7u_N000359",
        "v7u_N000360",
        "v7u_N000361",
        "v7u_N000362"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000363",
          "unit_type": "case",
          "cp_unit_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000360",
          "unit_type": "fact",
          "cp_unit_role": "explains"
        },
        {
          "unit_id": "v7u_N000362",
          "unit_type": "case",
          "cp_unit_role": "prescribes_measure"
        },
        {
          "unit_id": "v7u_N000356",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000357",
          "unit_type": "fact",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000358",
          "unit_type": "fact",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000359",
          "unit_type": "fact",
          "cp_unit_role": "illustrates"
        },
        {
          "unit_id": "v7u_N000361",
          "unit_type": "case",
          "cp_unit_role": "illustrates"
        }
      ]
    }
  ],
  "same_section_core_point_edges": []
}
```

section_text_with_unit_anchors:

```text
[v7u_N000356|356] In 2012, HSBC was involved in a money laundering scandal that remains one of the most significant AML compliance failures in banking history. Due to inadequate transaction monitoring and an overall fragmented and ineffective compliance framework, HSBC allowed drug cartels to launder over US$880 million in its Mexico operations.
ZH: 汇丰银行因反洗钱合规失败卷入洗钱丑闻，允许贩毒集团洗钱超过8.8亿美元

[v7u_N000357|357] In response to the breach, US federal regulators imposed a record fine of US$1.9 billion, which was the largest AML penalty at that time, comprising US$665 million in civil penalties.
ZH: 美国监管机构对汇丰处以19亿美元创纪录反洗钱罚款

[v7u_N000358|358] The US Department of Justice entered into a five-year deferred prosecution agreement with HSBC, mandating a comprehensive overhaul of its global compliance operations.
ZH: 美国司法部与汇丰达成五年延期起诉协议，要求全面整改全球合规

[v7u_N000359|359] One critical outcome of the investigation was the forced resignation of several senior executives, including the Global Head of Compliance, reflecting the regulator’s strong criticism of the bank’s AFC culture.
ZH: 调查导致汇丰多名高管辞职，包括全球合规主管，反映监管对金融犯罪防控文化的批评

[v7u_N000360|360] Regulators highlighted that HSBC’s internal environment had often prioritized local business interests and profit over robust, centralized compliance controls.
ZH: 监管指出汇丰内部环境常将本地业务和利润置于合规控制之上

[v7u_N000361|361] The operational repercussions were profound. Not only did the scandal trigger an immediate regulatory and financial backlash, but it also inflicted lasting reputational damage. HSBC’s credibility was severely undermined, leading to a significant erosion of customer trust and a weakened market position.
ZH: 汇丰银行丑闻导致监管处罚、财务损失和声誉损害，削弱客户信任和市场地位。

[v7u_N000362|362] As a corrective measure, the bank was compelled to rebalance power dynamics within its organization, strengthening central oversight and compliance functions while limiting the autonomy of local business units. This restructuring aimed to restore the integrity of its financial crime risk management framework and reduce exposure to high-risk jurisdictions through a strategic de-risking process.
ZH: 汇丰银行采取纠正措施，加强中央监督和合规职能，限制地方业务部门自主权，并通过去风险化减少高风险司法管辖区敞口。

[v7u_N000363|363] Ultimately, the HSBC case offers a severe lesson on the operational and reputational risks associated with weak financial crime controls. It underscores the critical importance of maintaining a strong compliance culture and implementing robust AML controls. It also serves as an instructive example for financial institutions worldwide: neglect in these areas not only results in severe financial penalties and operational disruption but also irrevocably damages a bank’s reputation, ultimately undermining its long-term viability in the global market.
ZH: 汇丰案例警示：薄弱的金融犯罪控制会导致运营和声誉风险，强调强合规文化与反洗钱控制的重要性。
```

allowed_unit_ids:

```json
[
  "v7u_N000356",
  "v7u_N000357",
  "v7u_N000358",
  "v7u_N000359",
  "v7u_N000360",
  "v7u_N000361",
  "v7u_N000362",
  "v7u_N000363"
]
```

original_json:

```json
{
  "section_id": "CH05-S02",
  "section_title": "Financial crime risks in relation to other types of risks > Case example: A lasting lesson",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N000356",
        "v7u_N000357",
        "v7u_N000358",
        "v7u_N000362"
      ],
      "proposition": "HSBC洗钱丑闻及监管处罚触发银行采取纠正措施，加强中央监督、限制地方自主权并实施去风险化，重构金融犯罪风险管理框架",
      "decision": "p7c_card",
      "card_id": "p7card_CH05_S02_001",
      "reason": "该有向链表达了外部事件触发特定应对动作并产生配置变化，超出基础KG的事实列举，可用于判断选项中的因果和措施"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000359",
        "v7u_N000360",
        "v7u_N000361",
        "v7u_N000363"
      ],
      "proposition": "高管辞职、监管批评、声誉损害等后果及总结教训，属于案例背景和事实，无明确的识别、评估、决策或应对的有向结构",
      "decision": "kg_only",
      "card_id": null,
      "reason": "这些单元提供原因、并列后果或总结，基础KG可充分表达为事实或教训，不存在可供选项判断的局部程序性或判断性有向链"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH05_S02_001",
      "section_id": "CH05-S02",
      "card_nature": "execution",
      "title": "汇丰银行纠正措施：加强中央监督、限制地方自主权与去风险化",
      "flow_nodes": [
        {
          "node_id": "E1",
          "node_category": "entry",
          "node_type": "E1_event_signal",
          "label": "HSBC洗钱丑闻曝光并遭受19亿美元罚款及五年延期起诉协议要求全面整改",
          "evidence_unit_ids": [
            "v7u_N000356",
            "v7u_N000357",
            "v7u_N000358"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P1",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "HSBC被迫执行纠正措施：重新平衡内部权力，加强中央监督和合规职能，限制地方业务部门自主权，并通过战略性去风险化减少高风险司法管辖区敞口",
          "evidence_unit_ids": [
            "v7u_N000362"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X1",
          "node_category": "exit",
          "node_type": "X5_config_change",
          "label": "HSBC金融犯罪风险管理框架重构：中央监督加强，地方自主权受限，去风险化实施（旨在恢复完整性并减少敞口）",
          "evidence_unit_ids": [
            "v7u_N000362"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "PRECEDES",
          "source": "E1",
          "target": "P1",
          "evidence_unit_ids": [
            "v7u_N000356",
            "v7u_N000357",
            "v7u_N000358",
            "v7u_N000362"
          ],
          "derivation": "explicit_text",
          "source_quote": "As a corrective measure, the bank was compelled to rebalance power dynamics... (v7u_N000362)"
        },
        {
          "edge_id": "e2",
          "edge_type": "PRODUCES",
          "source": "P1",
          "target": "X1",
          "evidence_unit_ids": [
            "v7u_N000362"
          ],
          "derivation": "explicit_text",
          "source_quote": "This restructuring aimed to restore the integrity of its financial crime risk management framework and reduce exposure to high-risk jurisdictions... (v7u_N000362)"
        }
      ],
      "source_unit_ids": [
        "v7u_N000356",
        "v7u_N000357",
        "v7u_N000358",
        "v7u_N000362"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：HSBC洗钱丑闻及监管处罚触发银行执行纠正措施，导致金融犯罪风险管理框架重构（加强中央监督、限制地方自主权、去风险化）。KG不足：基础KG可保存案例事实，但无法表达从外部事件到具体应对措施再到配置变化的有向判断链。选项判断：可确认或排除关于汇丰后丑闻应对措施、组织结构变化的选项。LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```
