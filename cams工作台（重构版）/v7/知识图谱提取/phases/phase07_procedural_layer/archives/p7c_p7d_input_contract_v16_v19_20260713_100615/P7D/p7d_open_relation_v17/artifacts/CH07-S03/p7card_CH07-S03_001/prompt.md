# P7D Flow Edge Evidence Review Prompt v1

## 角色与边界

你是P7D独立边级证据审核器。P7C已经生成候选card；你的任务是逐条审核card中的现有`flow_edge`，不是重新抽取card。

不得新增、删除、改写、拆分或连接card、node或edge。不得修改P7C正本。不得读取或假设具体题目、选项、参考答案或其他section内容。只输出严格JSON，不输出Markdown或解释。

`section_text_with_unit_anchors`和`section_units`是唯一事实证据。只能引用`allowed_unit_ids`中的unit_id。P7C card、label、source_quote、derivation以及旧版evidence_strength都只是待审核声明，不能反过来充当证据。

## 逐边审核问题

对每条现有edge分别检查：

1. `source_node_support`：source节点表达的主体、对象、动作、状态或结论是否有当前section依据。
2. `target_node_support`：target节点是否有当前section依据。
3. `direction_support`：原文是否支持source到target的方向；反向是否同样可能。
4. `condition_support`：edge的condition是否被原文明示支持。没有condition时填`not_applicable`。
5. `qualifier_support`：must、should、may、might、could、often、only、not、unless、potentially等限定是否被保留，是否被强化或弱化。没有相关限定时可以填`not_applicable`。
6. `parallel_or_correlation_check`：是否把并列来源、共同结果、相关关系、教材叙述顺序或一般主题关系错误写成`PRECEDES`、`PRODUCES`、`DECIDES`或`FEEDBACK`。

每项`status`只能是：`supported, pending, unsupported, not_applicable`。每项必须用中文填写`reason`。

## edge_type审核口径

- `PRECEDES`：只有原文明示顺序，或交换方向会违反唯一必要功能依赖时才成立。共同出现和教材顺序不成立。
- `REFERENCES`：只表达process对非时序输入、线索、标准或判断维度的参照，不表达先后或产出。
- `PRODUCES`：process必须产生target结果；揭示既存状态不等于产生该状态。
- `DECIDES`：必须存在真实条件分流，condition有原文证据；单一条件应对不自动构成分支。
- `FEEDBACK`：结果或事件必须触发复核、补充、更新、调优、监控或再次处理。

相邻句中的冻结、查封、调查、起诉、定罪、监禁和罚款不自动形成单链。多个线索、标准、情报来源或共同结果不因排列顺序形成先后边。

## derivation与建议

`derivation`只描述这条边如何由证据得到，不能用来代替审核结论：

- `explicit_text`：原文明示关系及方向。
- `llm_inference`：两端均有证据，但关系或方向依赖必要功能推理。
- `unsupported`：至少一端、关系、方向或条件缺少依据。

`llm_recommendation`只能是：

- `accepted`：所有必要检查均有充分支持。
- `pending`：存在歧义，或关系依赖必要功能推理，需要人工判断。
- `rejected`：至少一个关键检查明确不成立。

不要为了保留card而接受边。也不要因为边来自P7C或标为`explicit`就默认接受。

## 输出合同

必须覆盖输入card中的每一条edge，edge_id不得遗漏、增加或重复。顺序与输入保持一致。

```json
{
  "section_id": "CH07-S03",
  "card_id": "<card_id>",
  "edge_reviews": [
    {
      "edge_id": "<existing edge_id>",
      "derivation": "explicit_text",
      "llm_recommendation": "accepted",
      "checks": {
        "source_node_support": {"status": "supported", "reason": "<中文>"},
        "target_node_support": {"status": "supported", "reason": "<中文>"},
        "direction_support": {"status": "supported", "reason": "<中文>"},
        "condition_support": {"status": "not_applicable", "reason": "该边没有condition。"},
        "qualifier_support": {"status": "supported", "reason": "<中文>"},
        "parallel_or_correlation_check": {"status": "supported", "reason": "<中文>"}
      },
      "evidence_unit_ids": ["<allowed unit id>"],
      "source_quotes": ["<当前section原文短引>"],
      "reason": "<中文总判断>"
    }
  ]
}
```

## 当前section与card

section_id: `CH07-S03`
section_title: `Money laundering risks associated with retail and commercial banking > Credit-related product risks`

section_text_with_unit_anchors:
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

section_units:
[
  {
    "en_quote": "Credit-related products are fundamental to customer propositions in retail and commercial banking.",
    "knowledge_zh": "信贷相关产品是零售和商业银行客户服务的基础",
    "pdf_page": 72,
    "printed_page": "67",
    "type": "fact",
    "unit_id": "v7u_N000546",
    "unit_order": 546
  },
  {
    "en_quote": "Lending products, a subset of credit-related products, include personal loans, home ownership finance, and secured and unsecured loans.",
    "knowledge_zh": "贷款产品包括个人贷款、住房融资及有担保和无担保贷款",
    "pdf_page": 72,
    "printed_page": "67",
    "type": "classification",
    "unit_id": "v7u_N000547",
    "unit_order": 547
  },
  {
    "en_quote": "Personal loans help banks build customer relationships, while home ownership finance and secured loans can be a significant source of revenue and capital, respectively.",
    "knowledge_zh": "个人贷款有助于建立客户关系，住房融资和有担保贷款分别是重要的收入和资本来源",
    "pdf_page": 72,
    "printed_page": "67",
    "type": "fact",
    "unit_id": "v7u_N000548",
    "unit_order": 548
  },
  {
    "en_quote": "They are essential financial services that enable individuals and businesses to achieve their goals, drive economic growth, and promote financial stability.",
    "knowledge_zh": "信贷相关产品是促进经济增长和金融稳定的基本金融服务",
    "pdf_page": 72,
    "printed_page": "67",
    "type": "fact",
    "unit_id": "v7u_N000549",
    "unit_order": 549
  },
  {
    "en_quote": "Secured and unsecured loans are crucial for businesses, offering the necessary capital to expand operations, invest in new projects, and manage cash flow effectively.",
    "knowledge_zh": "有担保和无担保贷款为企业扩张、投资和现金流管理提供必要资本",
    "pdf_page": 72,
    "printed_page": "67",
    "type": "fact",
    "unit_id": "v7u_N000550",
    "unit_order": 550
  },
  {
    "en_quote": "However, credit-related products also present substantial money laundering risks.",
    "knowledge_zh": "信贷相关产品也带来重大的洗钱风险",
    "pdf_page": 72,
    "printed_page": "67",
    "type": "fact",
    "unit_id": "v7u_N000551",
    "unit_order": 551
  },
  {
    "en_quote": "Early loan repayment is one method used by criminals to disguise the origin of illicit funds. By repaying loans ahead of schedule, criminals can convert illegal proceeds into ostensibly legitimate funds. This tactic complicates the detection of suspicious activity, as early repayments do not inherently indicate wrongdoing and can often be viewed as a sign of financial health.",
    "knowledge_zh": "提前还贷是犯罪分子将非法资金伪装为合法资金的手段",
    "pdf_page": 72,
    "printed_page": "67",
    "type": "risk_indicator",
    "unit_id": "v7u_N000552",
    "unit_order": 552
  },
  {
    "en_quote": "Banks often face significant challenges when attempting to close customer accounts due to money laundering concerns, while the customer still owes money on credit-related products. One of the primary difficulties is the potential need to write off the loan balance, which creates a financial loss for the bank. This situation can lead to the following complications:",
    "knowledge_zh": "因洗钱担忧关闭客户账户时，若客户仍有贷款余额，银行面临财务损失等挑战",
    "pdf_page": 72,
    "printed_page": "67",
    "type": "classification",
    "unit_id": "v7u_N000553",
    "unit_order": 553
  },
  {
    "en_quote": "Recovery of funds: If the bank knows or suspects the customer is using illicit funds to repay the loan, the risk of default becomes a secondary risk to manage. The bank should not accept funds for the purposes of loan",
    "knowledge_zh": "若银行知道或怀疑客户使用非法资金还贷，不应接受该资金用于还贷",
    "pdf_page": 72,
    "printed_page": "67",
    "type": "fact",
    "unit_id": "v7u_N000554",
    "unit_order": 554
  },
  {
    "en_quote": "Risk appetite: When exiting customer relationships that fall outside the bank's risk tolerance, the loan balance complicates the process, as writing off a loan is a significant financial decision, often requiring extensive justification and approval.",
    "knowledge_zh": "退出超出风险容忍度的客户关系时，贷款余额使核销成为重大财务决策",
    "pdf_page": 73,
    "printed_page": "68",
    "type": "fact",
    "unit_id": "v7u_N000555",
    "unit_order": 555
  },
  {
    "en_quote": "Reputational risk: Failure to effectively manage these challenges can damage the bank's reputation and erode trust with regulators and customers, impacting long-term business operations and compliance standing.",
    "knowledge_zh": "未能有效管理这些挑战会损害银行声誉并削弱监管机构和客户的信任",
    "pdf_page": 73,
    "printed_page": "68",
    "type": "fact",
    "unit_id": "v7u_N000556",
    "unit_order": 556
  }
]

allowed_unit_ids:
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

p7c_card_under_review:
{
  "card_id": "p7card_CH07-S03_001",
  "section_id": "CH07-S03",
  "card_nature": "control",
  "title": "银行不应接受非法资金还贷",
  "flow_nodes": [
    {
      "node_id": "E1_KNOW_SUSPECT",
      "node_category": "entry",
      "node_type": "E1_event_signal",
      "label": "银行知道或怀疑客户使用非法资金还贷",
      "evidence_unit_ids": [
        "v7u_N000554"
      ],
      "evidence_strength": "explicit"
    },
    {
      "node_id": "P8_NOT_ACCEPT",
      "node_category": "process",
      "node_type": "P8_constrained_action",
      "label": "银行不应接受该资金用于贷款偿还",
      "evidence_unit_ids": [
        "v7u_N000554"
      ],
      "evidence_strength": "explicit"
    }
  ],
  "flow_edges": [
    {
      "edge_id": "EDGE_001",
      "edge_type": "PRECEDES",
      "source": "E1_KNOW_SUSPECT",
      "target": "P8_NOT_ACCEPT",
      "evidence_unit_ids": [
        "v7u_N000554"
      ],
      "derivation": "explicit_text"
    }
  ],
  "source_unit_ids": [
    "v7u_N000554"
  ],
  "candidate_status": "candidate",
  "review_notes": "增量命题：如果银行知道或怀疑非法资金还贷 → 银行不应接受该资金用于还贷；KG不足：基础KG不能表达这一条件触发的具体银行应对义务；选项判断：可帮助判断银行在可疑还贷时是否应接受资金；LLM推理：无。"
}
