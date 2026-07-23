<!-- allowed_unit_ids is intentionally not sent to the model. Unit IDs remain
     visible in section_text_with_unit_anchors and are validated by the Runner. -->

# P7C-S1.2 候选 Card Frame 独立补漏 v1

## 阶段角色

你是 **P7C-S1.2：候选 card frame 独立补漏器**。

S1.1 已经生成一组候选。你必须重新阅读完整 section，并将原文中所有可能合格的 frame 与 S1.1 候选逐项比较。只输出 S1.1 没有承接的候选；不得删除、改写或重复输出已有候选。

你不做 KG 边界裁决，不构建 flow node 或 flow edge，也不输出审核结论。你的输出与 S1.1 合并后才进入 S2。

## 候选 Card Frame 定义

候选 frame 是 section 内有原文证据支持的局部程序或判断单元。它围绕一个中心处理、判断、法律适用或归责组织；原文提供时，应同时纳入相关的触发/情境、输入/标准、依据/条件、结果、分支或后续行动。

```text
触发 / 情境 / 输入 / 标准 / 条件
                  -> 中心处理 / 判断 / 法律适用 / 归责
                  -> 结果 / 分支 / 后续行动
```

中心字段必有，且触发/依据/结果三类外围角色中至少有一类。上述概念图不要求三段齐全：原文仅支持“标准或条件 -> 具体处理/判断”，或“调查/审查动作 -> 发现/结论”时，允许开放候选，不得补造入口或出口。

这里的有向关系不等于时间顺序或因果关系，也可以是条件、判断标准、处理所参照的输入、法律适用、分支或反馈。必须保留原文中的 if、when、unless、may、might、could、should、must、only、not 等限定。

## 独立扫描与比对

在内部完成以下步骤，不输出扫描台账或推理过程：

1. 按自然段、主体变化、对象变化、案例事实、调查或审查动作、法律规则、条件、结果和例外扫描完整 section，先独立识别全部潜在 frame。
2. 围绕中心处理或判断组织 frame。前文已有候选不能成为停止扫描后文的理由。
3. 将每个独立识别的 frame 与全部 S1.1 候选比较。核心处理/判断及其关键证据已被同一候选覆盖时，视为已承接；只有主题相同但遗漏独立处置链、法律适用链或调查发现链时，仍视为缺口。
4. 只为未承接的 frame 输出 gap proposition。

## 必须识别的候选类型

- **同中心判断链**：同一对象的输入、计算、适用标准和正反结果应合并。例如，直接持股、间接持股、适用阈值与是否认定 UBO 属于同一判断 frame。
- **阈值设定与阈值适用**：风险为本地设定或调整阈值，与使用既有阈值判断具体对象，是不同中心，可以分别形成候选。
- **案例法律适用链**：案件事实、主体关系、地点或指控引发法律适用、管辖、责任或监管关切时，应输出“案例情境 -> 法律适用/归责判断 -> 原文结果（如有）”。通用法律规则不能替代案例中的实际适用候选。
- **调查发现链**：具名主体进行调查、审查、审计、筛查、分析或跟进并得出发现、结论、分类或升级时，应输出“调查/判断动作 -> 发现/结论”。
- **条件处置链**：if、when、unless、requires 等条件导向特定动作、禁止、批准、升级或结果时，应保留条件和情态。

## 不构成候选的内容

不输出纯定义、分类、产品列表、控制组成列表、孤立阈值、孤立红旗、普通案例事实或没有特定判断/应对的一般机制。

正例：

- `分析师初步调查 -> 发现高风险中间人安排`
- `案例主体关系和指控 -> 引发域外法律适用关切`
- `退出超出风险容忍度且仍有贷款余额的客户 -> 核销通常需要充分理由和批准`

反例：

- `公司使用中间人`
- `犯罪分子通过复杂网络洗钱`
- `受益所有权阈值通常为25%`

这些事实若没有原文中的机构动作、适用判断、条件化结果或特定应对，不单独形成候选。

## 合并边界

- 围绕同一中心处理/判断、同一对象且能由原文直接连读的材料合并为一个 frame。
- 不同中心处理/判断、不同业务目标或没有原文连接的材料分开。
- 只有相邻文本不足以跨 unit 合并；必须存在连接词、指代、共享中心判断或可验证的规则与正反例证据链。
- 不得仅换一种措辞重复 S1.1 候选。

## 证据合同

`section_text_with_unit_anchors`是唯一事实证据。只能引用锚点中可见的 unit ID。

- 每个`unit_id`必须由`evidence_spans`中的一项覆盖。
- 每个`evidence_spans.quote`必须是对应 unit 中精确、连续、可定位的原文短引。
- 每个`source_quotes`条目必须与某个`evidence_spans.quote`完全一致。
- `relation_cues`保留原文关系词；没有字面连接词时，填写能够体现原文关系的短语，不得留空。
- 只有跨 unit 归纳规则及其正反例时，`induction`填写`cross_unit`，并在`cross_unit_basis`中列出规则、正例和反例 unit；否则两者均为`null`。

## 输出 Contract

只输出严格 JSON。顶层字段为`section_id`和`gap_propositions`。

每个 gap proposition 必须保留 S1.1 的全部字段，并增加`gap_evidence`：

```json
{
  "section_id": "CH07-S03",
  "gap_propositions": [
    {
      "candidate_id": "s1c_gap_ch07_s03_writeoff_approval",
      "unit_ids": ["v7u_N000555"],
      "proposition": "退出超出银行风险容忍度且仍有贷款余额的客户关系时，核销贷款通常需要充分理由和批准。",
      "source_quotes": [
        "When exiting customer relationships that fall outside the bank's risk tolerance, the loan balance complicates the process, as writing off a loan is a significant financial decision, often requiring extensive justification and approval."
      ],
      "relation_cues": ["When", "requiring"],
      "candidate_frame": {
        "trigger_or_context": ["退出超出银行风险容忍度且仍有贷款余额的客户关系"],
        "basis_or_condition": ["核销是重大财务决策"],
        "focal_handling_or_judgment": "决定是否核销贷款余额并履行相应审批要求",
        "outcomes_or_paths": ["核销通常需要充分理由和批准"]
      },
      "evidence_spans": [
        {
          "unit_id": "v7u_N000555",
          "quote": "When exiting customer relationships that fall outside the bank's risk tolerance, the loan balance complicates the process, as writing off a loan is a significant financial decision, often requiring extensive justification and approval."
        }
      ],
      "induction": null,
      "cross_unit_basis": null,
      "gap_evidence": {
        "compared_with_candidate_ids": ["s1c_ch07_s03_illicit_repayment"],
        "gap_reason": "已有候选只承接怀疑非法资金还贷时不得接受资金，没有承接退出客户且仍有贷款余额时核销通常需要理由和批准这一独立处置链。"
      }
    }
  ]
}
```

`candidate_id`必须以`s1c_gap_`开头，且不得与 S1.1 ID 重复。

`gap_evidence.compared_with_candidate_ids`只能引用输入中的 S1.1 候选 ID；S1.1 列表非空时至少列出一个最相关候选。若 S1.1 为空，可以使用空数组。`gap_reason`必须用中文说明缺失的中心处理/判断及已有候选为何没有承接。

如果独立扫描后确认没有遗漏，输出：

```json
{"section_id":"<section_id>","gap_propositions":[]}
```

## 当前section

section_id: `CH02-S05`

section_title: `Types of financial crime > Key takeaways`

section_text_with_unit_anchors:

```text
[v7u_N000145|145] Multinationals using intermediaries in high-risk areas face increased bribery risks.
ZH: 在高风险地区使用中介的跨国公司面临更高的贿赂风险

[v7u_N000146|146] Corporate bribery often involves third parties, shell companies, and false invoicing.
ZH: 企业贿赂常涉及第三方、壳公司和虚假发票

[v7u_N000147|147] Illicit funds are frequently laundered to conceal their origin.
ZH: 非法资金常被洗钱以掩盖其来源

[v7u_N000148|148] Financial institutions should:
ZH: 金融机构应采取以下措施

[v7u_N000149|149] Conduct audits to identify control deficiencies.
ZH: 进行审计以识别控制缺陷

[v7u_N000150|150] Enhance transaction monitoring for suspicious activities, especially regarding “consultancy fees” to individuals or intermediaries located in high-risk jurisdictions.
ZH: 加强对高风险地区咨询费的可疑交易监控

[v7u_N000151|151] Include anti-bribery clauses for customers engaging in intermediary models.
ZH: 对采用中介模式的客户加入反贿赂条款

[v7u_N000152|152] Tax avoidance, or tax planning, is not illegal. It is the activity of legitimately reducing the amount of tax owed to government by legal or natural persons.
ZH: 避税是合法减少税负的行为

[v7u_N000153|153] Some jurisdictions encourage tax avoidance by allowing pre-tax savings.
ZH: 一些司法管辖区通过允许税前储蓄来鼓励避税

[v7u_N000154|154] Tax evasion is the use of illegal practices to avoid paying a tax liability.
ZH: 逃税是使用非法手段逃避纳税义务

[v7u_N000155|155] This could include not declaring taxable income or hiding taxable assets from the authorities.
ZH: 逃税示例：不申报应税收入或隐藏应税资产

[v7u_N000156|156] Tax evasion is illegal and those caught are generally subject to criminal charges and substantial penalties.
ZH: 逃税违法，将面临刑事指控和重大处罚

[v7u_N000157|157] While tax avoidance is legal and causes financial services firms no concerns, aggressive tax avoidance is defined as the aggressive legal interpretation of the law without adequately considering its intent or spirit.
ZH: 激进避税是激进地解释法律而不考虑其意图或精神

[v7u_N000158|158] An example of aggressive tax avoidance is a multinational company requiring its subsidiaries to pay a royalty fee for the use of its intellectual property. This reduces the profitability of the overseas unit and therefore reduces the tax they pay in that jurisdiction.
ZH: 激进避税示例：跨国公司要求子公司支付知识产权使用费以减少利润和税款

[v7u_N000159|159] AFC professionals should be satisfied that a customer’s activities across an account fall within avoidance parameters.
ZH: 金融犯罪防控专业人员应确保客户活动在避税参数范围内

[v7u_N000160|160] Tax evasion is illegal and is considered a predicate offense for money laundering.
ZH: 逃税是洗钱的上游犯罪

[v7u_N000161|161] A predicate offense is a component part of a more serious crime.
ZH: 上游犯罪是更严重犯罪的组成部分。

[v7u_N000162|162] Information gathered at onboarding and during transaction monitoring should inform the activity the organization should expect across the customer’s account.
ZH: 开户和交易监控数据应告知机构对客户账户的预期活动。

[v7u_N000163|163] Unusual activity such as excessive personal expense claims across a small business account might be a warning signal that a customer is evading tax.
ZH: 小企业账户中过度的个人费用报销可能是逃税的警告信号。

[v7u_N000164|164] The Common Reporting Standard (CRS), developed in response to the G-20 countries' request and approved by the OECD (Organization for Economic Cooperation and Development) Council, calls on jurisdictions to obtain information from their financial institutions and automatically exchange that information with other jurisdictions on an annual basis. It sets out the financial account information to be exchanged, the financial institutions required to report, the different types of accounts and taxpayers covered, as well as common due diligence procedures to be followed by financial institutions. Its purpose is to combat tax evasion.
ZH: 共同申报准则（CRS）要求司法管辖区每年自动交换金融账户信息以打击逃税。

[v7u_N000165|165] Fraud is an intentional act of criminal deception in order to obtain an unjust or illegal advantage. Typically, fraud results in financial or personal gain. Notice that fraud is intentional and uses deception to achieve the goal.
ZH: 欺诈是为获取不正当利益而故意进行的欺骗行为。

[v7u_N000166|166] Fraud can be committed by one or more individuals—from low-level employees, to management, to government officials. It can be found in every country and every type of business.
ZH: 欺诈可由个人或多人实施，存在于各国和各行业。

[v7u_N000167|167] Knowing the common features of fraud, as well as typical motivations and red flags, will help you combat this crime.
ZH: 了解欺诈的常见特征、动机和红旗信号信号有助于打击此类犯罪。

[v7u_N000168|168] People commit fraud for three major reasons: pressure, opportunity, and rationalization. This three-sided model is referred to as the “Fraud Triangle.”
ZH: 欺诈三角模型指出欺诈的三个主要原因：压力、机会和合理化。

[v7u_N000169|169] Pressure is sometimes called "incentive." It can be a financial problem that drives a person to commit fraud, such as gambling or other debt. This can create the pressure to commit fraud.
ZH: 压力（或诱因）是驱动个人实施欺诈的财务问题，如赌博债务。

[v7u_N000170|170] Opportunity is often provided by a lack of effective internal controls within an institution. For example, confidential documents are left unattended in the office.
ZH: 机会通常由机构内部缺乏有效的内部控制提供。

[v7u_N000171|171] Rationalization is when the fraudster convinces herself that what she is doing does not really matter or that the fraud is justified.
ZH: 合理化是欺诈者说服自己行为无关紧要或正当的过程。

[v7u_N000172|172] There are many different types of fraud, or schemes, each of which has its own unique red flags. Common red flags of fraud include:
ZH: 欺诈有多种类型，每种都有独特的红旗信号信号，常见红旗信号包括：

[v7u_N000173|173] Something sounds too good to be true
ZH: 听起来好得令人难以置信。

[v7u_N000174|174] A promise of high returns for low investment
ZH: 承诺低投资高回报。

[v7u_N000175|175] Demand for upfront payments
ZH: 要求预先付款。

[v7u_N000176|176] Deliberate creation of an artificial shortage of opportunities
ZH: 故意制造人为的机会稀缺。

[v7u_N000177|177] Element of secrecy
ZH: 保密元素。

[v7u_N000178|178] Sense of urgency
ZH: 紧迫感。

[v7u_N000179|179] Pressure to act...right now!
ZH: 立即行动的压力。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000148",
      "v7u_N000149",
      "v7u_N000150",
      "v7u_N000151"
    ],
    "proposition": "金融机构应通过审计、交易监控和反贿赂条款来应对高风险中介带来的贿赂风险。",
    "source_quotes": [
      "Financial institutions should:",
      "Conduct audits to identify control deficiencies.",
      "Enhance transaction monitoring for suspicious activities, especially regarding “consultancy fees” to individuals or intermediaries located in high-risk jurisdictions.",
      "Include anti-bribery clauses for customers engaging in intermediary models."
    ],
    "relation_cues": [
      "should",
      "especially",
      "regarding"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "在高风险地区使用中介的跨国公司面临更高的贿赂风险"
      ],
      "basis_or_condition": [
        "高风险区域的中介和咨询费"
      ],
      "focal_handling_or_judgment": "金融机构采取审计、监控和合同条款措施",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000148",
        "quote": "Financial institutions should:"
      },
      {
        "unit_id": "v7u_N000149",
        "quote": "Conduct audits to identify control deficiencies."
      },
      {
        "unit_id": "v7u_N000150",
        "quote": "Enhance transaction monitoring for suspicious activities, especially regarding “consultancy fees” to individuals or intermediaries located in high-risk jurisdictions."
      },
      {
        "unit_id": "v7u_N000151",
        "quote": "Include anti-bribery clauses for customers engaging in intermediary models."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N000159"
    ],
    "proposition": "金融犯罪防控专业人员应确保客户活动在避税参数范围内。",
    "source_quotes": [
      "AFC professionals should be satisfied that a customer’s activities across an account fall within avoidance parameters."
    ],
    "relation_cues": [
      "should",
      "fall within"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "客户账户活动"
      ],
      "basis_or_condition": [
        "避税参数"
      ],
      "focal_handling_or_judgment": "确保客户活动在避税参数内",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000159",
        "quote": "AFC professionals should be satisfied that a customer’s activities across an account fall within avoidance parameters."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N000162"
    ],
    "proposition": "机构应利用开户和交易监控信息形成对客户账户的预期活动。",
    "source_quotes": [
      "Information gathered at onboarding and during transaction monitoring should inform the activity the organization should expect across the customer’s account."
    ],
    "relation_cues": [
      "should",
      "inform"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "开户和交易监控信息"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "形成对客户账户的预期活动",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000162",
        "quote": "Information gathered at onboarding and during transaction monitoring should inform the activity the organization should expect across the customer’s account."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N000163"
    ],
    "proposition": "小企业账户中过度的个人费用报销可能是逃税的警告信号。",
    "source_quotes": [
      "Unusual activity such as excessive personal expense claims across a small business account might be a warning signal that a customer is evading tax."
    ],
    "relation_cues": [
      "might",
      "warning signal"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "小企业账户中过度的个人费用报销"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "识别为逃税的警告信号",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000163",
        "quote": "Unusual activity such as excessive personal expense claims across a small business account might be a warning signal that a customer is evading tax."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
