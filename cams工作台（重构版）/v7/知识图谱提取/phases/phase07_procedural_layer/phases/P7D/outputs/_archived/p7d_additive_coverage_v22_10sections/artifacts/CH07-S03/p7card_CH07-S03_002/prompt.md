# P7D Flow Edge Evidence Review Prompt v1

## 角色与边界

你是P7D独立边级证据审核器。P7C已经生成候选card；你的任务是逐条审核card中的现有`flow_edge`，不是重新抽取card。

不得新增、删除、改写、拆分或连接card、node或edge。不得修改P7C正本。不得读取或假设具体题目、选项、参考答案或其他section内容。只输出严格JSON，不输出Markdown或解释。

`section_text_with_unit_anchors`是唯一事实证据。只能引用`allowed_unit_ids`中的unit_id。P7C card中的节点、label、edge、condition和relation_type都只是待审核声明，不能反过来充当证据。

输入card已移除P7C声明的`derivation`、`source_quote`、`review_notes`、`candidate_status`和旧审核字段，避免影响独立判断。你必须仅根据当前section原文重新判断审核用`derivation`；Runner会在LLM审核完成后，另行结合未暴露给你的P7C声明生成最终状态。

## 逐边审核问题

对每条现有edge分别检查：

1. `source_node_support`：source节点表达的主体、对象、动作、状态或结论是否有当前section依据。
2. `target_node_support`：target节点是否有当前section依据。
3. `direction_support`：原文是否支持source到target的方向；反向是否同样可能。
4. `condition_support`：edge的condition是否被原文明示支持。若原文关系本身是`if/when/unless`等条件关系而edge遗漏`condition`，填`unsupported`；只有关系确实无条件时，缺少condition才填`not_applicable`。
5. `qualifier_support`：must、should、may、might、could、often、only、not、unless、potentially等限定是否被保留，是否被强化或弱化。没有相关限定时可以填`not_applicable`。
6. `parallel_or_correlation_check`：是否把并列来源、共同结果、相关关系、教材叙述顺序或一般主题关系错误写成`PRECEDES`、`PRODUCES`、`DECIDES`或`FEEDBACK`。

每项`status`只能是：`supported, pending, unsupported, not_applicable`。每项必须用中文填写`reason`。

## edge_type审核口径

- `PRECEDES`：只有原文明示顺序，或交换方向会违反唯一必要功能依赖时才成立。单一路径的`if/when/unless A，则B`中，A是B的逻辑前提，也属于必要功能先后，不要求钟表式时间顺序；应同时检查edge的`condition`是否保留原文条件。共同出现和教材顺序不成立。
- `REFERENCES`：只表达process对非时序输入、线索、标准或判断维度的参照，不表达先后、产出或条件分支。若带`condition`，它只能限定该参照关系的适用范围，并必须有原文证据。
- `PRODUCES`：process必须产生target结果；揭示既存状态不等于产生该状态。
- `DECIDES`：必须存在真实条件分流，condition有原文证据；单一条件应对不自动构成分支。
- `FEEDBACK`：结果或事件必须触发复核、补充、更新、调优、监控或再次处理。

相邻句中的冻结、查封、调查、起诉、定罪、监禁和罚款不自动形成单链。多个线索、标准、情报来源或共同结果不因排列顺序形成先后边。

`REFERENCES`不要求原文必须出现字面上的“参照/使用”。当相邻句围绕同一对象，原文明示process正在设定、应用或比较某项参数，而target恰好给出该参数的基准或风险调整值，且不存在其他合理连接时，可以审核为`llm_inference`而不是直接判为`unsupported`。若只是同主题并列或存在多种合理连接，仍应拒绝或待审。

`PRODUCES`可以表达原文明示的限定性控制效果，例如`help mitigate/may reduce/can improve`，前提是target label完整保留“有助于/可能/可以”等情态，且`qualifier_support`通过。`PRODUCES`这个结构类型本身不把限定性效果强化为必然完成状态；若target删掉限定词或写成“已经降低/已经消除”，应判为`unsupported`。

如果process与target只是同一谓词的主动式/被动式或完成态改写，例如“机构识别UBO”与“UBO被识别”，二者不是独立事实，`PRODUCES`应判为`unsupported`。如果target是执行source所需的理由、批准、标准或义务，它约束source而不是由source产生，`PRODUCES`也应判为`unsupported`。

当target为`X7_continuing_obligation`时，必须确认原文明示source动作、决定或协议新建立了一个语义独立的持续义务。若target只是把source中的“必须/应当执行某动作”复制成义务出口，`PRODUCES`应判为`unsupported`。

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
  "card_id": "p7card_CH07-S03_002",
  "section_id": "CH07-S03",
  "title": "退出超出风险容忍度客户时核销贷款通常需要理由和批准",
  "card_nature": "execution",
  "source_unit_ids": [
    "v7u_N000555",
    "v7u_N000553"
  ],
  "flow_nodes": [
    {
      "node_id": "N1",
      "node_category": "process",
      "node_type": "P2_execution",
      "label": "银行：核销贷款",
      "evidence_unit_ids": [
        "v7u_N000555"
      ]
    },
    {
      "node_id": "N2",
      "node_category": "auxiliary",
      "node_type": "standard",
      "label": "通常需要广泛理由和批准",
      "evidence_unit_ids": [
        "v7u_N000555"
      ]
    },
    {
      "node_id": "N3",
      "node_category": "entry",
      "node_type": "E6_change_exception",
      "label": "银行因洗钱担忧试图关闭有未偿贷款客户账户",
      "evidence_unit_ids": [
        "v7u_N000553"
      ]
    }
  ],
  "flow_edges": [
    {
      "edge_id": "E1",
      "edge_type": "REFERENCES",
      "source": "N1",
      "target": "N2",
      "relation_type": "standard_constrains_action",
      "condition": "当退出超出风险容忍度的客户关系且存在贷款余额时",
      "evidence_unit_ids": [
        "v7u_N000555"
      ]
    },
    {
      "edge_id": "E2",
      "edge_type": "PRECEDES",
      "source": "N3",
      "target": "N1",
      "condition": "当试图关闭账户且客户仍有未偿贷款时",
      "evidence_unit_ids": [
        "v7u_N000553"
      ]
    }
  ]
}
