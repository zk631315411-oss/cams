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

section_id: `CH11-S02`

section_title: `Money laundering risks associated with MSBs, payment service providers, and ecommerce > Money services business`

section_text_with_unit_anchors:

```text
[v7u_N000813|813] A money service business (MSB) is a type of nonbank financial institution that provides financial services involving the transfer of money or value.
ZH: 货币服务企业是提供货币或价值转移服务的非银行金融机构

[v7u_N000814|814] An entity is an MSB if it holds funds on behalf of another person or entity.
ZH: 若实体代他人持有资金，则被视为货币服务企业

[v7u_N000815|815] In many jurisdictions, MSBs are required to comply with local regulatory AML and CFT requirements. These requirements can include registering with local regulators and establishing an AML compliance program.
ZH: 许多司法辖区要求货币服务企业遵守反洗钱和反恐怖融资规定，包括注册和建立合规计划

[v7u_N000816|816] MSB services vary according to their licensing requirement. Examples of MSB services include:
ZH: 货币服务企业的服务因牌照要求而异，以下为示例列表

[v7u_N000817|817] Currency exchange
ZH: 货币服务企业的服务包括货币兑换

[v7u_N000818|818] Money transfers
ZH: 货币服务企业的服务包括汇款

[v7u_N000819|819] Money orders
ZH: 货币服务企业的服务包括汇票

[v7u_N000820|820] Stored-value products, such as prepaid cards or gift cards
ZH: 货币服务企业的服务包括储值产品，如预付卡或礼品卡

[v7u_N000821|821] Bill payment services
ZH: 货币服务企业提供的账单支付服务

[v7u_N000822|822] These services can be delivered through online platforms, mobile apps, or physical branches.
ZH: 货币服务企业服务可通过在线平台、移动应用或实体网点提供

[v7u_N000823|823] MSBs originally required licensing mainly for currency exchange, but the scope has expanded to include cross-border money transfers and additional services.
ZH: 货币服务企业许可范围从货币兑换扩展到跨境汇款及其他服务

[v7u_N000824|824] If a business participates in activities categorized as MSB services, it must obtain a license to operate legally.
ZH: 从事货币服务企业服务的企业必须获得许可才能合法运营

[v7u_N000825|825] Historically, MSBs were mainly used to serve individual customers’ crossborder transactions more quickly and cheaply.
ZH: 历史上货币服务企业主要用于为个人客户提供更快更便宜的跨境交易

[v7u_N000826|826] Today, MSBs also serve small and medium-sized businesses that are not served by larger financial institutions.
ZH: 如今货币服务企业也为大型金融机构服务不足的中小企业提供服务

[v7u_N000827|827] The changes in the usage of MSB licenses also bring stringent jurisdictional registration requirements and regulations.
ZH: 货币服务企业许可使用变化带来严格的司法注册要求和法规

[v7u_N000828|828] According to FinCEN, hawala is an informal value transfer system (IVTS), which is classified under the money transmitter category of MSBs.
ZH: FinCEN将哈瓦拉归类为非正式价值转移系统和货币服务企业中的货币转移商

[v7u_N000829|829] However, hawala differs from other, more traditional, MSBs in several ways. The primary distinction is that MSBs are regulated by the banking system, while hawala operates as an informal and largely unregulated method of money transfer.
ZH: 哈瓦拉与传统货币服务企业的主要区别在于监管：货币服务企业受银行体系监管，哈瓦拉为非正规且基本不受监管

[v7u_N000830|830] MSBs face complex jurisdictional licensing requirements, including varying fees and compliance obligations. Each jurisdiction may impose different AML regulations, which can create operational burdens and increase regulatory scrutiny. This complexity can lead to difficulties in maintaining compliance across multiple borders.
ZH: 货币服务企业面临复杂的司法许可要求，包括不同费用和反洗钱合规义务

[v7u_N000831|831] Noncompliance, intentional or accidental, might lead to severe penalties, including regulatory fines, consent orders, and even loss of business licenses.
ZH: 货币服务企业不合规可能导致监管罚款、同意令甚至吊销营业执照

[v7u_N000832|832] MSBs often serve customers or engage in business activities less likely to be supported by traditional financial institutions. These customers include individuals lacking access to mainstream banking services. However, customers without access to traditional banking services can pose challenges when assessing money laundering and terrorist financing risks. Some of these risks include:
ZH: 货币服务企业服务无银行账户客户带来的洗钱和恐怖融资风险

[v7u_N000833|833] Lack of financial history: Unbanked customers often lack financial records, making it difficult for MSBs to assess the legitimacy of their transactions.
ZH: 无银行账户客户缺乏财务记录，货币服务企业难以评估交易合法性

[v7u_N000834|834] Cash transactions: Unbanked individuals rely on cash, which can create vulnerabilities for MSBs, such as difficulty in tracking a high volume of transactions and ascertaining the source of these funds.
ZH: 无银行账户者依赖现金交易，给货币服务企业带来追踪和资金来源确认困难

[v7u_N000835|835] These risks typically fall outside the risk appetite of traditional financial institutions, particularly due to the substantial volume of cross-border remittances.
ZH: 这些风险通常超出传统金融机构的风险偏好，尤其是大量跨境汇款

[v7u_N000836|836] MSBs need to implement additional strategic money laundering and operational controls, such as enhanced due diligence. They should also limit the exposure to high-risk customers.
ZH: 货币服务企业需实施额外洗钱和运营控制，如强化尽职调查，并限制高风险客户敞口

[v7u_N000837|837] Cross-border transactions complicate compliance efforts. Different jurisdictions enforce varying laws regarding fund movement, currency controls, sanctions, and regulatory and tax reporting. Some countries implement strict restrictions on remittances, while others are more lenient.
ZH: 跨境交易因不同司法管辖区的资金流动、货币管制、制裁和税务报告法律而复杂化

[v7u_N000838|838] Establishing long-term and trusted relationships with correspondent banks can mitigate money laundering and compliance risks.
ZH: 与代理行建立长期信任关系可降低洗钱和合规风险

[v7u_N000839|839] A correspondent bank serves as an intermediary in international transactions, aiding the MSB in accessing banking services that might not be directly available to it because of its higher-risk customer base.
ZH: 代理行作为国际交易中介，帮助货币服务企业获得因高风险客户群而无法直接获得的银行服务

[v7u_N000840|840] Correspondent banks are required to assess the soundness of the MSB’s compliance program and ensure that the MSB’s activities align with the correspondent bank’s risk appetite.
ZH: 代理行需评估货币服务企业合规计划的健全性，并确保其活动符合代理行的风险偏好
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000814"
    ],
    "proposition": "An entity is an MSB if it holds funds on behalf of another person or entity.",
    "source_quotes": [
      "An entity is an MSB if it holds funds on behalf of another person or entity."
    ],
    "relation_cues": [
      "if",
      "is"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "entity holds funds on behalf of another"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "entity is classified as an MSB",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000814",
        "quote": "An entity is an MSB if it holds funds on behalf of another person or entity."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N000815"
    ],
    "proposition": "MSBs are required to comply with local AML/CFT requirements including registration and compliance program.",
    "source_quotes": [
      "In many jurisdictions, MSBs are required to comply with local regulatory AML and CFT requirements. These requirements can include registering with local regulators and establishing an AML compliance program."
    ],
    "relation_cues": [
      "required",
      "can include"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "entity is an MSB"
      ],
      "basis_or_condition": [
        "local regulatory requirements"
      ],
      "focal_handling_or_judgment": "comply with AML/CFT requirements",
      "outcomes_or_paths": [
        "register with local regulators",
        "establish AML compliance program"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000815",
        "quote": "In many jurisdictions, MSBs are required to comply with local regulatory AML and CFT requirements. These requirements can include registering with local regulators and establishing an AML compliance program."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N000824"
    ],
    "proposition": "If a business participates in MSB services, it must obtain a license to operate legally.",
    "source_quotes": [
      "If a business participates in activities categorized as MSB services, it must obtain a license to operate legally."
    ],
    "relation_cues": [
      "if",
      "must"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "business participates in MSB services"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "obtain a license to operate legally",
      "outcomes_or_paths": [
        "legal operation"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000824",
        "quote": "If a business participates in activities categorized as MSB services, it must obtain a license to operate legally."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N000831"
    ],
    "proposition": "Noncompliance by MSBs might lead to severe penalties including fines, consent orders, or loss of license.",
    "source_quotes": [
      "Noncompliance, intentional or accidental, might lead to severe penalties, including regulatory fines, consent orders, and even loss of business licenses."
    ],
    "relation_cues": [
      "might",
      "lead to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "noncompliance (intentional or accidental)"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "noncompliance leads to penalties",
      "outcomes_or_paths": [
        "regulatory fines",
        "consent orders",
        "loss of business licenses"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000831",
        "quote": "Noncompliance, intentional or accidental, might lead to severe penalties, including regulatory fines, consent orders, and even loss of business licenses."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N000836"
    ],
    "proposition": "MSBs need to implement additional controls such as enhanced due diligence and limit exposure to high-risk customers.",
    "source_quotes": [
      "MSBs need to implement additional strategic money laundering and operational controls, such as enhanced due diligence. They should also limit the exposure to high-risk customers."
    ],
    "relation_cues": [
      "need to",
      "should"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "MSB operations"
      ],
      "basis_or_condition": [
        "money laundering and operational risks"
      ],
      "focal_handling_or_judgment": "implement additional controls and limit exposure",
      "outcomes_or_paths": [
        "enhanced due diligence",
        "limiting high-risk customer exposure"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000836",
        "quote": "MSBs need to implement additional strategic money laundering and operational controls, such as enhanced due diligence. They should also limit the exposure to high-risk customers."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N000838"
    ],
    "proposition": "Establishing long-term trusted relationships with correspondent banks can mitigate money laundering and compliance risks.",
    "source_quotes": [
      "Establishing long-term and trusted relationships with correspondent banks can mitigate money laundering and compliance risks."
    ],
    "relation_cues": [
      "can",
      "mitigate"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "establish long-term trusted relationships with correspondent banks"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "mitigate money laundering and compliance risks",
      "outcomes_or_paths": [
        "reduced money laundering risk",
        "reduced compliance risk"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000838",
        "quote": "Establishing long-term and trusted relationships with correspondent banks can mitigate money laundering and compliance risks."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N000840"
    ],
    "proposition": "Correspondent banks are required to assess the MSB's compliance program and ensure alignment with the bank's risk appetite.",
    "source_quotes": [
      "Correspondent banks are required to assess the soundness of the MSB’s compliance program and ensure that the MSB’s activities align with the correspondent bank’s risk appetite."
    ],
    "relation_cues": [
      "required",
      "assess",
      "ensure"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "correspondent bank relationship with MSB"
      ],
      "basis_or_condition": [
        "regulatory requirements"
      ],
      "focal_handling_or_judgment": "assess MSB's compliance program and ensure alignment",
      "outcomes_or_paths": [
        "alignment with risk appetite"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000840",
        "quote": "Correspondent banks are required to assess the soundness of the MSB’s compliance program and ensure that the MSB’s activities align with the correspondent bank’s risk appetite."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
