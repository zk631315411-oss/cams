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

结构复杂度不是门槛。一个unit、一条路径、没有分支或反馈，都不能作为`kg_only`理由。entry是图中的关系起点，不要求是时间事件；业务对象、线索输入、风险阈值、监管要求或政策基准都可以承担有证据的入口角色。

以下通常应提升：

- 金融机构监控系统根据异常活动进行标记并形成识别结论。
- FIU综合SAR和跨境活动并形成红旗发现。
- 风险阈值和直接/间接持股被机构用于UBO判断并形成分类结论。
- 外部监管要求或上位标准触发机构调整控制、政策或职责。
- 明确条件触发拒绝、批准、升级、报告、监控、复核或持续义务。

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

新增card必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, review_status, review_notes`。

`card_nature`只能为：`execution, assessment, risk_indicator, control`。

每张新增card至少包含一个entry、process和exit，并存在entry经过process到exit的有向路径。

节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。节点必须由原文明示，`evidence_strength`只能为`explicit`。

允许节点类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

边必填：`edge_id, edge_type, source, target, evidence_unit_ids, evidence_strength`。允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

- `REFERENCES`只能由process指向auxiliary input或standard。
- `PRODUCES`只能由process指向exit。
- `DECIDES`只能由`P3_branch_routing`发出，至少两条分支，每条都有原文明示的`condition`。
- `functional_dependency`只允许用于边，且card必须为`needs_review`并在`review_notes`的“LLM推理”中说明。

默认省略`relation_type`。只有完全符合允许语义和端点约束时才填写，不得创造新类型。

必须保留`must, should, may, might, could, often, potentially, help`等情态强度。不得将“有助于缓解”强化为“风险已经消除”。

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
      "candidate_id": "cand_CH07-S03_001",
      "unit_ids": [
        "v7u_N000546",
        "v7u_N000547",
        "v7u_N000548",
        "v7u_N000549",
        "v7u_N000550",
        "v7u_N000551"
      ],
      "proposition": "信贷产品的一般介绍及其洗钱风险概述",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅为背景介绍和一般风险声明，无程序性或判断性有向结构"
    },
    {
      "candidate_id": "cand_CH07-S03_002",
      "unit_ids": [
        "v7u_N000552"
      ],
      "proposition": "提前还贷是犯罪分子将非法资金转换为合法资金的手段",
      "decision": "kg_only",
      "card_id": null,
      "reason": "孤立的洗钱方法/风险指标，无机构响应或判断链，基础KG即可表达"
    },
    {
      "candidate_id": "cand_CH07-S03_003",
      "unit_ids": [
        "v7u_N000553"
      ],
      "proposition": "因洗钱担忧关闭账户时，贷款余额导致核销等复杂情况",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅为上下文引介，具体程序性结构由后续单元表达"
    },
    {
      "candidate_id": "cand_CH07-S03_004",
      "unit_ids": [
        "v7u_N000554"
      ],
      "proposition": "如果银行知道或怀疑客户使用非法资金还贷，则银行不应接受该资金",
      "decision": "p7c_card",
      "card_id": "p7card_CH07-S03_001",
      "reason": "条件导向禁止动作形成程序性有向结构，可判断特定条件下银行的义务和应对"
    },
    {
      "candidate_id": "cand_CH07-S03_005",
      "unit_ids": [
        "v7u_N000555"
      ],
      "proposition": "退出超出风险容忍度客户且存在贷款余额时，核销贷款通常需要充分理由和批准",
      "decision": "p7c_card",
      "card_id": "p7card_CH07-S03_002",
      "reason": "情境条件导致核销决策须满足批准和理由要求，形成判断性有向结构"
    },
    {
      "candidate_id": "cand_CH07-S03_006",
      "unit_ids": [
        "v7u_N000556"
      ],
      "proposition": "未能有效管理关闭账户的挑战会损害银行声誉",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅描述一般风险后果，无程序性或判断性动作链"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH07-S03_001",
      "section_id": "CH07-S03",
      "card_nature": "control",
      "title": "银行知道或怀疑还贷资金非法时不应接受",
      "flow_nodes": [
        {
          "node_id": "n1",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "银行知道或怀疑客户使用非法资金还贷",
          "evidence_unit_ids": [
            "v7u_N000554"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "银行不应接受该资金用于还贷",
          "evidence_unit_ids": [
            "v7u_N000554"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n3",
          "node_category": "exit",
          "node_type": "X3_state_change",
          "label": "非法还贷资金未被接受",
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
          "source": "n1",
          "target": "n2",
          "evidence_unit_ids": [
            "v7u_N000554"
          ],
          "evidence_strength": "explicit"
        },
        {
          "edge_id": "e2",
          "edge_type": "PRODUCES",
          "source": "n2",
          "target": "n3",
          "evidence_unit_ids": [
            "v7u_N000554"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "source_unit_ids": [
        "v7u_N000554"
      ],
      "review_status": "accepted",
      "review_notes": "增量命题：银行知道或怀疑还贷资金非法 → 银行不应接受该资金 → 资金未被接受。基础KG不足：基础KG可整体保存该规则为事实，但不能表达条件→禁止动作→拒绝状态的有向判断链。选项判断：可用于确认在特定条件下银行的义务和应对措施。LLM推理：无。"
    },
    {
      "card_id": "p7card_CH07-S03_002",
      "section_id": "CH07-S03",
      "card_nature": "execution",
      "title": "退出超出风险容忍度客户且存在贷款余额时核销需批准",
      "flow_nodes": [
        {
          "node_id": "n1",
          "node_category": "entry",
          "node_type": "E6_change_exception",
          "label": "退出超出风险容忍度的客户关系且存在贷款余额",
          "evidence_unit_ids": [
            "v7u_N000555"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n2",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "银行进行贷款核销",
          "evidence_unit_ids": [
            "v7u_N000555"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "n3",
          "node_category": "exit",
          "node_type": "X7_continuing_obligation",
          "label": "核销贷款通常需要充分理由和批准",
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
          "source": "n1",
          "target": "n2",
          "evidence_unit_ids": [
            "v7u_N000555"
          ],
          "evidence_strength": "functional_dependency"
        },
        {
          "edge_id": "e2",
          "edge_type": "PRODUCES",
          "source": "n2",
          "target": "n3",
          "evidence_unit_ids": [
            "v7u_N000555"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "source_unit_ids": [
        "v7u_N000555"
      ],
      "review_status": "needs_review",
      "review_notes": "增量命题：退出超出风险容忍度客户且存在贷款余额 → 银行进行贷款核销 → 核销通常需要充分理由和批准。基础KG不足：基础KG可保存核销需要批准的事实，但不能表达情境→核销决策→批准要求的程序链。选项判断：可用于判断在退出客户且存在贷款余额时，银行的决策和批准要求。LLM推理：边e1为functional_dependency，原文未直接说明退出情境然后进行核销，但退出客户且存在贷款余额必然导致考虑核销，该方向是完成原文所述业务功能所必需。"
    }
  ],
  "skip_reason": null
}
```
