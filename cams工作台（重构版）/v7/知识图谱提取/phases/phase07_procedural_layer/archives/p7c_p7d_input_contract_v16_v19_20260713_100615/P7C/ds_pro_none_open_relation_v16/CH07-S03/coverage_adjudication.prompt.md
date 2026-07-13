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
2. 候选内部存在“情境/事件/线索/输入/标准 → 主体动作或判断 → 结果/义务/控制效果”的局部结构。
3. 该方向结构能够帮助判断选项的顺序、条件、主体职责、义务、应对、因果或适用范围。
4. 基础KG只能保存整句话或各知识点，不能充分表达句内的主体、方向、条件及动作结果关系。

结构复杂度和是否闭环不是门槛。一个unit、一条路径、没有分支或反馈，或没有独立出口，都不能作为`kg_only`理由。entry是图中的关系起点，不要求是时间事件；业务对象、线索输入、风险阈值可以承担入口角色；被动作参照的监管要求、政策基准或风险偏好应作为auxiliary standard/input并由process通过`REFERENCES`指向。

不得用“纯义务陈述”“没有复杂条件”“没有复杂步骤”拒绝提升。只要候选已经明确给出监管要求、风险偏好或状态变化如何约束特定主体的识别、标准选择或分类维持，并形成义务、配置或分类出口，就满足局部有向结构要求。

以下通常应提升：

- 金融机构监控系统根据异常活动进行标记并形成识别结论。
- FIU综合SAR和跨境活动并形成红旗发现。
- 风险阈值和直接/间接持股被机构用于UBO判断并形成分类结论。
- 外部监管要求或上位标准触发机构调整控制、政策或职责。
- 明确条件触发拒绝、批准、升级、报告、监控、复核或持续义务。
- 当地监管要求约束机构如何识别PEP并形成识别义务；不得因规则只有一个unit而拒绝。
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

section_id: `CH07-S03`

section_title: `Money laundering risks associated with retail and commercial banking > Credit-related product risks`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "core_points": [
    {
      "core_point_id": "cp_CH07_S03_001",
      "title_zh": "提前还贷作为洗钱手段",
      "title_en": "Early Loan Repayment as a Money Laundering Method",
      "anchor_unit_ids": [
        "v7u_N000552"
      ],
      "key_unit_ids": [
        "v7u_N000552"
      ],
      "support_unit_ids": [],
      "unit_roles": [
        {
          "unit_id": "v7u_N000552",
          "unit_type": "risk_indicator",
          "cp_unit_role": "describes_process"
        }
      ]
    },
    {
      "core_point_id": "cp_CH07_S03_002",
      "title_zh": "关闭有未偿信贷账户的挑战",
      "title_en": "Challenges in Closing Accounts with Outstanding Credit Balances",
      "anchor_unit_ids": [
        "v7u_N000554",
        "v7u_N000555",
        "v7u_N000556"
      ],
      "key_unit_ids": [
        "v7u_N000554",
        "v7u_N000555",
        "v7u_N000556",
        "v7u_N000553"
      ],
      "support_unit_ids": [
        "v7u_N000553"
      ],
      "unit_roles": [
        {
          "unit_id": "v7u_N000554",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000555",
          "unit_type": "fact",
          "cp_unit_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000556",
          "unit_type": "fact",
          "cp_unit_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000553",
          "unit_type": "classification",
          "cp_unit_role": "provides_context"
        }
      ]
    }
  ],
  "same_section_core_point_edges": [
    {
      "source_id": "cp_CH07_S03_001",
      "target_id": "cp_CH07_S03_002",
      "relation_type": "prepares",
      "reason": "CP1 describes early loan repayment as a money laundering method, which sets the stage for CP2's discussion of the challenges banks face when closing accounts with outstanding credit balances, as the illicit repayment creates the outstanding balance complication."
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

original_json:

```json
{
  "section_id": "CH07-S03",
  "section_title": "Money laundering risks associated with retail and commercial banking > Credit-related product risks",
  "coverage_audit": [
    {
      "candidate_id": "cand_001",
      "unit_ids": [
        "v7u_N000546"
      ],
      "proposition": "信贷相关产品是零售和商业银行客户服务的基础",
      "decision": "kg_only",
      "card_id": null,
      "reason": "背景介绍，无程序性或判断性有向结构"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000547"
      ],
      "proposition": "贷款产品类型包括个人贷款、住房融资及有担保和无担保贷款",
      "decision": "kg_only",
      "card_id": null,
      "reason": "基础定义和分类，KG足以表达"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000548"
      ],
      "proposition": "个人贷款帮助建立客户关系，住房融资和有担保贷款是收入和资本来源",
      "decision": "kg_only",
      "card_id": null,
      "reason": "产品好处陈述，无程序性结构"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000549"
      ],
      "proposition": "信贷相关产品是促进经济增长和金融稳定的基本金融服务",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般重要性描述，无程序性结构"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000550"
      ],
      "proposition": "有担保和无担保贷款为企业提供资本用于扩张、投资和现金流管理",
      "decision": "kg_only",
      "card_id": null,
      "reason": "产品功能陈述，无程序性结构"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N000551"
      ],
      "proposition": "信贷相关产品也带来重大的洗钱风险",
      "decision": "kg_only",
      "card_id": null,
      "reason": "风险概述，无具体有向判断链"
    },
    {
      "candidate_id": "cand_007",
      "unit_ids": [
        "v7u_N000552"
      ],
      "proposition": "提前还贷是犯罪分子将非法资金伪装为合法资金的手段",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅描述犯罪分子的洗钱方法，属风险指标，无机构应对或判断结构"
    },
    {
      "candidate_id": "cand_008",
      "unit_ids": [
        "v7u_N000553"
      ],
      "proposition": "因洗钱担忧关闭账户时，若客户仍有贷款余额，银行面临财务损失等挑战",
      "decision": "kg_only",
      "card_id": null,
      "reason": "情境引入，概述挑战，未形成具体条件-动作-结果链"
    },
    {
      "candidate_id": "cand_009",
      "unit_ids": [
        "v7u_N000554"
      ],
      "proposition": "若银行知道或怀疑客户使用非法资金还贷，则银行不应接受该资金用于还贷",
      "decision": "p7c_card",
      "card_id": "p7card_CH07-S03_001",
      "reason": "明确条件触发银行的具体禁止性应对（不应接受），构成条件-动作的判断性增量结构"
    },
    {
      "candidate_id": "cand_010",
      "unit_ids": [
        "v7u_N000555"
      ],
      "proposition": "退出超出风险容忍度的客户关系且客户有贷款余额时，核销贷款决策通常需要充分理由和批准",
      "decision": "p7c_card",
      "card_id": "p7card_CH07-S03_002",
      "reason": "明确条件约束下的核销决策需理由和批准的程序性要求，构成条件-动作-结果增量结构"
    },
    {
      "candidate_id": "cand_011",
      "unit_ids": [
        "v7u_N000556"
      ],
      "proposition": "未能有效管理这些挑战会损害银行声誉并削弱信任",
      "decision": "kg_only",
      "card_id": null,
      "reason": "后果说明，无具体主体应对或程序性结构"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH07-S03_001",
      "section_id": "CH07-S03",
      "card_nature": "execution",
      "title": "银行在知道或怀疑非法资金还贷时不应接受还款",
      "flow_nodes": [
        {
          "node_id": "E1_001",
          "node_category": "entry",
          "node_type": "E1_event_signal",
          "label": "银行知道或怀疑客户使用非法资金偿还贷款",
          "evidence_unit_ids": [
            "v7u_N000554"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P2_001",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "银行不应接受该资金用于还贷",
          "evidence_unit_ids": [
            "v7u_N000554"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "PRECEDES",
          "source": "E1_001",
          "target": "P2_001",
          "evidence_unit_ids": [
            "v7u_N000554"
          ],
          "derivation": "explicit_text",
          "source_quote": "If the bank knows or suspects the customer is using illicit funds to repay the loan, ... The bank should not accept funds for the purposes of loan"
        }
      ],
      "source_unit_ids": [
        "v7u_N000554"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：银行知道或怀疑非法资金还贷 → 银行不应接受还款；KG不足：基础KG可表述“不应接受非法资金还贷”的事实，但未能表达该条件触发特定主体拒绝动作的程序性结构；选项判断：可确认或排除关于银行在特定条件下接受或拒绝还款的选项；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH07-S03_002",
      "section_id": "CH07-S03",
      "card_nature": "execution",
      "title": "退出超出风险容忍度客户时核销贷款需充分理由和批准",
      "flow_nodes": [
        {
          "node_id": "E6_002",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "银行退出超出风险容忍度的客户关系，且客户存在贷款余额",
          "evidence_unit_ids": [
            "v7u_N000555"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P2_002",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "银行作出核销贷款决策",
          "evidence_unit_ids": [
            "v7u_N000555"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "X3_002",
          "node_category": "exit",
          "node_type": "X3_state_change",
          "label": "核销决策通常需要充分理由和批准",
          "evidence_unit_ids": [
            "v7u_N000555"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "e1",
          "edge_type": "PRECEDES",
          "source": "E6_002",
          "target": "P2_002",
          "evidence_unit_ids": [
            "v7u_N000555"
          ],
          "derivation": "explicit_text",
          "source_quote": "When exiting customer relationships that fall outside the bank's risk tolerance, the loan balance complicates the process"
        },
        {
          "edge_id": "e2",
          "edge_type": "PRODUCES",
          "source": "P2_002",
          "target": "X3_002",
          "evidence_unit_ids": [
            "v7u_N000555"
          ],
          "derivation": "explicit_text",
          "source_quote": "as writing off a loan is a significant financial decision, often requiring extensive justification and approval"
        }
      ],
      "source_unit_ids": [
        "v7u_N000555"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：退出超出风险容忍度客户且有贷款余额 → 核销决策通常需要充分理由和批准；KG不足：基础KG可记录退出时贷款余额使核销复杂，但未表达核销决策具体需要理由和批准的程序性要求；选项判断：可确认或排除关于核销决策是否需要理由和批准的选项；LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```
