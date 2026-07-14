# P7C Section-Local Additive Coverage Review Prompt v3

## 角色

你是P7C section级增量完整性审查器。首次抽取器已经输出候选命题和候选card，这些card尚未经过P7D正式结构校验和边级审核。首次结果可能出现三类问题：把P7C关系误判为`kg_only`、把同一关系的前提和应对拆到不同候选、或在已有card中漏画节点和边。

你的任务是在完整检查当前section后输出只增式JSON补丁。准确率仍然重要，但P7C是候选层，允许把有充分当前section证据的边交给P7D继续审核。不得为了减少候选数量而遗漏基础KG无法表达的条件、方向、主体动作或独立结果。

`original_json`提供本次无记忆API调用所需的完整首次抽取上下文。不得回显、删除或改写它。Runner只会执行受保护的追加操作。只输出严格JSON，不输出Markdown或解释。

## P7C目的与KG边界

P7C不重复基础KG已经能够充分表达的定义、分类、事实、普通案例、孤立风险指标、一般规则、普通机制因果和组成关系。P7C增量表达：业务情境、事件、线索、输入或标准如何关联到特定主体带原文情态的识别、评估、决策或应对，以及原文明示的独立结论、记录、状态变化、控制效果、分支或后续行动。

基础KG能保存整句话或分别保存两个知识点，不代表它已经表达句内或句间的条件、主体、方向、动作约束和独立结果。没有独立结果时允许开放式局部关系。

P7C不读取题目或参考答案，不处理跨section桥接。`section_text_with_unit_anchors`是唯一事实证据；`base_kg_section_summary`只用于去重。所有新增证据只能引用`allowed_unit_ids`。

## 三项审查

### 一、复核原`kg_only`候选

对`review_target_candidate_ids`中的每个候选逐一裁决。可以保持`kg_only`，也可以将其关联到新增card或已有card的补充内容。

### 二、重新扫描完整section

按自然段落、转折、主体、对象和条件变化重新扫描原文。即使首次抽取没有登记候选，也必须检查是否存在遗漏关系。

重点检查：

- 相邻或邻近unit分别给出条件/变化与动作/应对，首次抽取却拆成两个`kg_only`候选；
- `if, when, unless, even if, based on, require, must, should, may, monitor, identify, review, approval, escalate, trigger, result in, help`等表达；
- 输入、线索、判断维度或标准被特定主体用于识别、评估、阈值选择或处置；
- 动作产生语义独立的结论、记录、状态变化或带原文限定的控制效果；
- 已有card覆盖了主题，但遗漏后文的新对象、条件、结果或应对。

允许跨越首次候选边界，允许合并多个候选的unit，也允许使用首次候选完全未登记的当前section unit。不得跨section取证。

### 三、检查已有card的图表达完整性

逐张比较`original_json.cards`、其对应`coverage_audit.proposition`与原文：

- proposition中的条件、参照关系和独立结果是否都进入`flow_nodes + flow_edges`；
- 结果是否只藏在process标签中而没有结果节点和边；
- 多个判断输入是否只被列出，却没有通过`REFERENCES`连接到评估动作；
- 方向错误的已有边是否需要追加一条证据支持的正确关系。

只能追加节点、边和`source_unit_ids`。不得删除、修改、重新编号或替换已有card、节点或边。已有错误边留给P7D拒绝；可以追加正确的替代边，新增边仍须由P7D审核。

## 成卡标准

新增关系必须同时满足：

1. 当前section证据支持关系两端、主体、方向和条件（如有）。
2. 关系超出基础KG能充分表达的定义、事实、列表、普通机制或一般知识关系。
3. 关系能帮助判断选项的顺序、条件、职责、义务、应对、适用范围或限定性结果。
4. 不需要补造主体、动作、条件或结果。

相邻句之间缺少明确连接词，但存在必要功能依赖时，可以输出`derivation=llm_inference`，交P7D和人工复核；不得伪装为`explicit_text`。

不得以“纯义务陈述”“没有复杂步骤”或“只受风险偏好约束”为由跳过已经具备主体、动作和方向的关系。

以下通常保持`kg_only`：纯定义/分类/阈值数值/组成列表、普通犯罪手法、孤立红旗、普通案例事实、一般机制因果、抽象风险缓解目的，以及必须补造主体或方向才能成立的关系。

特别地，“当局调查非法活动时受到腐败官员阻挠”只有调查困难和犯罪机制，不是金融机构/监管主体的识别、评估、决策或应对链，必须保持`kg_only`。不要因为句子含有`investigate`、`block`或`hinder`就自动成卡。

后续unit如果只是独立事实、犯罪性质说明、处罚或背景结果，不能仅因位于某个process之后就追加为该process的`PRODUCES`目标。只有原文明确说明同一动作产生该结果，或存在必要功能依赖时，才允许建立边；否则保留为KG内容。

调优、控制或框架组成的定义、目标和一般效果通常由KG承接；只有具体主体基于明确输入执行创建/修改/删除、监控、评估或应对动作时，才进入P7C。

## 重点回归边界

- “不断演变的法规可能与现有业务模式和控制错位；合规计划必须持续更新”：两句共同形成变化/错位到更新应对的候选，`unit_ids`必须覆盖两句；没有明确连接词时边标记`llm_inference`，不能把两句分别留给KG。
- “部分机构采用一旦PEP永远PEP，因为个人即使卸任仍可能保持影响力”：不得写成“卸任`PRECEDES`机构采用方法”。应把“部分机构维持PEP分类”作为process，把“卸任后仍可能保有影响力”作为input并用`REFERENCES`表达理由/判断依据，同时保留“部分机构、即使、可能”。
- “其他机构考察个人影响力和PEP分类时间”：评估动作应通过`REFERENCES`连接两个判断输入，即使没有独立出口也可以成卡。
- “高风险客户的受益所有权阈值可能降至10%或5%”：高风险适用条件必须进入关系的`condition`或明确的条件节点和边，不能只埋在“适用阈值”节点标签中。
- “持续监控基于预定义标准标记交易，并有助于识别异常模式”：标准约束和带`help`限定的识别结果都应进入图。
- “资产管理人的CDD流程要求了解所有交易参与方”：CDD动作应通过`REFERENCES`连接所需参与方信息。

不得把“识别并核实控制人”再连接到“控制人已识别”这种主动式/被动式同义出口。不得把FIU红旗、案件升级、执法监控和资产冻结仅按教材顺序重新串成总链；只有原文明示的局部触发或结果边才可追加。

## 图规则

新增完整card和card补充使用相同图规则。

节点必填：`node_id, node_category, node_type, label, evidence_unit_ids, evidence_strength`。节点必须由原文明示，`evidence_strength`只能为`explicit`。

允许节点类型：

- entry：`E1_event_signal, E2_object_entry, E3_state_threshold, E4_handoff, E5_time_cycle, E6_change_exception, E7_external_command, E8_decision_finding`
- process：`P1_assessment, P2_execution, P3_branch_routing, P4_collection, P5_coordination, P6_feedback, P7_monitoring, P8_constrained_action, P9_planning, P10_sufficiency`
- exit：`X1_classification, X2_product, X3_state_change, X4_handoff, X5_config_change, X6_termination, X7_continuing_obligation`
- auxiliary：`input, standard`

边必填：`edge_id, edge_type, source, target, evidence_unit_ids, derivation`。允许：`PRECEDES, REFERENCES, PRODUCES, DECIDES, FEEDBACK`。

- `REFERENCES`只能由process指向auxiliary input或standard，不表达先后或产出。
- `PRODUCES`只能由process指向语义独立的exit。
- 单一路径条件使用带`condition`的`PRECEDES`；只有至少两条原文明示路径才使用`DECIDES`。
- `DECIDES`只能由`P3_branch_routing`发出。
- `derivation`只能为`explicit_text`或`llm_inference`。

静态适用对象、材料、因素、阈值、监管要求或风险偏好不得仅因语法顺序建成`entry --PRECEDES--> process`；应作为input/standard，由process通过`REFERENCES`指向。不得把同一谓词的主动式和被动式拆成动作和结果，不得把动作所需的批准、理由、标准或要求/义务写成`PRODUCES`。

`REFERENCES.condition`只限定input/standard适用于process的范围，不表达条件分支。单一路径`PRECEDES.condition`表达逻辑前提，不要求钟表式先后。

必须保留`must, should, may, might, could, often, potentially, help, typically`等情态和限定。`help mitigate`只能写成“有助于缓解”，不能写成必然降低。`must`本身不证明义务是持续、定期、永久或反复的。`X7_continuing_obligation`只用于原文明示新建立的独立持续义务，规范性动作仍保留在process中。

`escalate/escalation`默认写成“升级处理/升级处置”或保留英文，不得翻译为“上报/报告”；只有原文明示`report/notify/file/refer`及对象时才能写成报告或移交。

默认省略`relation_type`。只有完全符合允许语义和端点约束时才填写。

## 补丁合同

顶层必须且只能包含：

```text
section_id
coverage_adjudication
new_candidates
new_cards
card_supplements
```

### coverage_adjudication

对每个`review_target_candidate_ids`恰好输出一条：

```json
{
  "candidate_id": "cand_001",
  "original_decision": "kg_only",
  "final_decision": "kg_only",
  "card_id": null,
  "reason": "<中文>"
}
```

`final_decision`只能是`kg_only`或`p7c_card`。提升时`card_id`必须指向`new_cards`中的新card，或指向被`card_supplements`补充的已有card。多个候选可以共同指向同一card。

### new_candidates

用于记录跨候选关系、首次未登记的关系或已有card的遗漏关系。每项必填：

```json
{
  "candidate_id": "coverage_gap_001",
  "unit_ids": ["<当前section unit_id>"],
  "proposition": "<完整有向命题>",
  "decision": "p7c_card",
  "card_id": "<新增或被补充的card_id>",
  "reason": "<KG不能表达什么>",
  "origin_candidate_ids": ["<相关首次候选ID，可为空>" ]
}
```

新`candidate_id`不得与`original_json.coverage_audit`重复。`unit_ids`可以是多个原候选unit的并集，也可以包含首次未登记的当前section unit。

### new_cards

只放新增完整card。每张必填：`card_id, section_id, card_nature, title, flow_nodes, flow_edges, source_unit_ids, candidate_status, review_notes`。`card_nature`只能为`execution, assessment, risk_indicator, control`；不得输出`local_process`等自造值。`candidate_status`固定为`candidate`。card ID不得与已有card重复。每张新card必须被某条提升裁决或`new_candidates`引用。

### card_supplements

只用于给已有card追加内容：

```json
{
  "patch_id": "coverage_supplement_001",
  "card_id": "<已有card_id>",
  "reason": "<中文说明遗漏>",
  "origin_candidate_ids": ["<相关首次候选ID或本补丁new_candidate ID，可为空>"],
  "add_flow_nodes": [],
  "add_flow_edges": [],
  "add_source_unit_ids": []
}
```

至少新增一个节点或一条边。新增ID不得与该card已有ID重复。新增边可以连接已有节点和新增节点。所有新增节点、边的证据unit必须已经存在于card的`source_unit_ids`，或同时列入`add_source_unit_ids`。每个被补充的card必须由一条提升裁决或`new_candidates`引用。

没有某类修改时输出空数组。即使`review_target_candidate_ids`为空，仍必须扫描完整section、审核已有card，并输出五个顶层字段。

## 输出骨架

```json
{
  "section_id": "<section_id>",
  "coverage_adjudication": [],
  "new_candidates": [],
  "new_cards": [],
  "card_supplements": []
}
```

## 当前section

section_id: `CH07-S03`

section_title: `Money laundering risks associated with retail and commercial banking > Credit-related product risks`

base_kg_section_summary:

```json
{
  "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
  "covered_topics": [
    {
      "title_zh": "提前还贷作为洗钱手段",
      "title_en": "Early Loan Repayment as a Money Laundering Method",
      "covered_units": [
        {
          "unit_id": "v7u_N000552",
          "unit_type": "risk_indicator",
          "kg_role": "describes_process"
        }
      ]
    },
    {
      "title_zh": "关闭有未偿信贷账户的挑战",
      "title_en": "Challenges in Closing Accounts with Outstanding Credit Balances",
      "covered_units": [
        {
          "unit_id": "v7u_N000554",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000555",
          "unit_type": "fact",
          "kg_role": "indicates_risk"
        },
        {
          "unit_id": "v7u_N000556",
          "unit_type": "fact",
          "kg_role": "states_consequence"
        },
        {
          "unit_id": "v7u_N000553",
          "unit_type": "classification",
          "kg_role": "provides_context"
        }
      ]
    }
  ],
  "covered_relations": [
    {
      "source_title": "提前还贷作为洗钱手段",
      "target_title": "关闭有未偿信贷账户的挑战",
      "relation_type": "prepares"
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
        "v7u_N000552"
      ],
      "proposition": "提前还贷是犯罪分子将非法资金伪装为合法资金的手段",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅描述洗钱方法，无机构识别、评估或应对结构，基础KG可将其作为风险指标保存。"
    },
    {
      "candidate_id": "cand_002",
      "unit_ids": [
        "v7u_N000554"
      ],
      "proposition": "如果银行知道或怀疑客户使用非法资金还贷，则银行不应接受该资金用于还贷",
      "decision": "p7c_card",
      "card_id": "p7card_CH07-S03_001",
      "reason": "条件导向的明确应对动作，形成条件-禁止性行为的有向结构，超出基础KG的一般知识表达。"
    },
    {
      "candidate_id": "cand_003",
      "unit_ids": [
        "v7u_N000555"
      ],
      "proposition": "当退出超出风险容忍度的客户关系时，核销贷款通常需要充分理由和批准",
      "decision": "p7c_card",
      "card_id": "p7card_CH07-S03_002",
      "reason": "特定退出场景下核销动作的约束条件，形成有向的‘场景→动作约束’关系，基础KG无法表达该条件化链接。"
    },
    {
      "candidate_id": "cand_004",
      "unit_ids": [
        "v7u_N000553"
      ],
      "proposition": "因洗钱担忧关闭客户账户时，若客户仍有贷款余额，银行面临潜在核销和财务损失等挑战",
      "decision": "kg_only",
      "card_id": null,
      "reason": "仅陈述困难与后果，无明确动作或判断有向结构，属于背景性事实。"
    },
    {
      "candidate_id": "cand_005",
      "unit_ids": [
        "v7u_N000556"
      ],
      "proposition": "未能有效管理这些挑战会损害银行声誉并削弱监管机构和客户信任",
      "decision": "kg_only",
      "card_id": null,
      "reason": "一般风险后果陈述，无具体程序性或判断性有向链。"
    },
    {
      "candidate_id": "cand_006",
      "unit_ids": [
        "v7u_N000546",
        "v7u_N000547",
        "v7u_N000548",
        "v7u_N000549",
        "v7u_N000550",
        "v7u_N000551"
      ],
      "proposition": "信贷相关产品是基本金融服务，但也带来洗钱风险",
      "decision": "kg_only",
      "card_id": null,
      "reason": "主题引入与一般风险陈述，无局部程序性或判断性有向结构。"
    }
  ],
  "cards": [
    {
      "card_id": "p7card_CH07-S03_001",
      "section_id": "CH07-S03",
      "card_nature": "control",
      "title": "知道或怀疑非法资金还贷时银行不应接受还款",
      "flow_nodes": [
        {
          "node_id": "E1",
          "node_category": "entry",
          "node_type": "E8_decision_finding",
          "label": "银行知道或怀疑客户使用非法资金还贷",
          "evidence_unit_ids": [
            "v7u_N000554"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "P1",
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
          "edge_id": "E1_to_P1",
          "edge_type": "PRECEDES",
          "source": "E1",
          "target": "P1",
          "evidence_unit_ids": [
            "v7u_N000554"
          ],
          "derivation": "explicit_text",
          "condition": "银行知道或怀疑客户使用非法资金还贷",
          "source_quote": "If the bank knows or suspects the customer is using illicit funds to repay the loan, ... The bank should not accept funds for the purposes of loan"
        }
      ],
      "source_unit_ids": [
        "v7u_N000554"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：银行知道或怀疑非法资金还贷 → 银行不应接受该资金（条件触发禁止性动作）；KG不足：基础KG不能表达条件导向的具体应对动作的有向关系；选项判断：可确认在知道或怀疑非法资金时，银行应采取禁止接受还款的应对措施；LLM推理：无。"
    },
    {
      "card_id": "p7card_CH07-S03_002",
      "section_id": "CH07-S03",
      "card_nature": "control",
      "title": "退出超出风险容忍度的客户时核销贷款需充分理由和批准",
      "flow_nodes": [
        {
          "node_id": "P1",
          "node_category": "process",
          "node_type": "P2_execution",
          "label": "银行核销贷款",
          "evidence_unit_ids": [
            "v7u_N000555"
          ],
          "evidence_strength": "explicit"
        },
        {
          "node_id": "S1",
          "node_category": "auxiliary",
          "node_type": "standard",
          "label": "通常需要充分理由和批准",
          "evidence_unit_ids": [
            "v7u_N000555"
          ],
          "evidence_strength": "explicit"
        }
      ],
      "flow_edges": [
        {
          "edge_id": "P1_to_S1",
          "edge_type": "REFERENCES",
          "source": "P1",
          "target": "S1",
          "evidence_unit_ids": [
            "v7u_N000555"
          ],
          "derivation": "explicit_text",
          "relation_type": "standard_constrains_action",
          "condition": "退出超出风险容忍度的客户关系时",
          "source_quote": "When exiting customer relationships that fall outside the bank's risk tolerance, ... writing off a loan is a significant financial decision, often requiring extensive justification and approval."
        }
      ],
      "source_unit_ids": [
        "v7u_N000555"
      ],
      "candidate_status": "candidate",
      "review_notes": "增量命题：退出超出风险容忍度的客户时，银行核销贷款（动作）受约束于需要充分理由和批准（标准）；KG不足：基础KG可以表达核销需要理由这一事实，但不能表达该约束与特定退出场景的条件化关联；选项判断：可确认在退出超出容忍度的客户时，核销贷款需要额外审批要求；LLM推理：无。"
    }
  ],
  "skip_reason": null
}
```

review_target_candidate_ids:

```json
[
  "cand_001",
  "cand_004",
  "cand_005",
  "cand_006"
]
```
