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

section_id: `CH10-S02`

section_title: `Money Laundering Risks in Nonbank Financial Institutions > Case example: CashBayou's risk management challenges`

section_text_with_unit_anchors:

```text
[v7u_N000768|768] CashBayou is a thriving e-commerce platform, connecting buyers and sellers across the globe. CashBayou’s platform is structured in such a way that they hold buyers’ funds temporarily and convert them into the sellers' preferred currency before transferring them to sellers. Because of this, they are required to have an MSB license.
ZH: 案例：CashBayou 作为电子商务平台因持有并转换资金而需持有 货币服务企业 牌照。

[v7u_N000769|769] CashBayou also works closely with payment service providers, payment aggregators, card issuers, and other financial entities to ensure smooth and efficient transactions and facilitate their ecommerce ecosystem.
ZH: CashBayou 与支付服务商、聚合器、发卡机构等合作以支持电子商务生态。

[v7u_N000770|770] CashBayou has a new head of AML compliance, Emma. On her second day on the job, she receives an alert about unusual transaction patterns. She quickly gathers her team to investigate.
ZH: CashBayou 新任反洗钱合规负责人 Emma 收到异常交易警报并召集团队调查。

[v7u_N000771|771] They discover that a new buyer, using multiple accounts, is making high-frequency, low-value transactions with a network of sellers who are all based in the same jurisdiction.
ZH: 发现新买家使用多个账户向同一司法管辖区的卖家进行高频低额交易。

[v7u_N000772|772] This raises a red flag for money laundering.
ZH: 该交易模式引发洗钱红旗信号信号。

[v7u_N000773|773] While investigating, Emma realizes CashBayou's current KYC governance and execution are inadequate.
ZH: Emma 发现 CashBayou 当前的 了解你的客户 治理和执行存在不足。

[v7u_N000774|774] Insufficient reviews of purchasers and storefront owners could expose the platform to financia crime, fraud risks, and potential regulatory issues, which might result in temporary service suspension.
ZH: 对买家和店主审查不足可能使平台面临金融犯罪、欺诈和监管风险。

[v7u_N000775|775] The company’s current primary payment service provider, PaySecure, which is an E-Money License Institution (EMI) registered in the UK, contacts Emma and requests more information on a series of transactions.
ZH: 主要支付服务商 PaySecure 联系 Emma 要求提供一系列交易的更多信息。

[v7u_N000776|776] Emma notices that the request covers part of the unusual transactions related to the new buyer.
ZH: Emma 注意到该请求涉及部分与新买家相关的异常交易。

[v7u_N000777|777] In addition, based on the frequency of transactions, PaySecure requests a cal with the compliance officer of CashBayou to understand their due diligence process.
ZH: PaySecure 要求与 CashBayou 合规官通话以了解其尽职调查流程。

[v7u_N000778|778] During the meeting, PaySecure expresses their concern on CashBayou’s policies and stresses the need for ongoing collaboration and rigorous monitoring to mitigate risks.
ZH: 会议中 PaySecure 对 CashBayou 的政策表示担忧，强调持续合作和严格监控。

[v7u_N000779|779] Later that week, Emma's team receives a letter from their card issuer partner, CardGuard. The letter states that companies using CardGuard’s services are required to align their due diligence procedures with CardGuard’s standards for referred cardholders. Failure to comply will result in the termination of CardGuard’s partnership with CashBayou.
ZH: 发卡机构 CardGuard 要求 CashBayou 调整尽职调查程序以符合其标准，否则终止合作。

[v7u_N000780|780] This example demonstrates how NBFIs, unlike traditional banks, need to navigate multifaceted relationships with various financial entities, each presenting unique compliance challenges. By proactively identifying and addressing AML and KYC deficiencies and fostering open communication with their partners, Emma aims to create a more secure transaction environment that protects both the platform, its partners, and its users from financial crime.
ZH: 案例说明非银行金融机构需处理多方关系，主动识别反洗钱和 了解你的客户 缺陷以防范金融犯罪。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000770",
      "v7u_N000771",
      "v7u_N000772",
      "v7u_N000773",
      "v7u_N000774"
    ],
    "proposition": "新任反洗钱合规负责人Emma收到异常交易警报后调查，发现新买家多账户高频低额交易模式引发洗钱红旗，并意识到当前KYC治理不足，审查不充分可能带来金融犯罪和监管风险。",
    "source_quotes": [
      "CashBayou has a new head of AML compliance, Emma. On her second day on the job, she receives an alert about unusual transaction patterns. She quickly gathers her team to investigate.",
      "They discover that a new buyer, using multiple accounts, is making high-frequency, low-value transactions with a network of sellers who are all based in the same jurisdiction.",
      "This raises a red flag for money laundering.",
      "While investigating, Emma realizes CashBayou's current KYC governance and execution are inadequate.",
      "Insufficient reviews of purchasers and storefront owners could expose the platform to financia crime, fraud risks, and potential regulatory issues, which might result in temporary service suspension."
    ],
    "relation_cues": [
      "alert",
      "investigate",
      "discover",
      "raises a red flag",
      "realizes",
      "could expose"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "收到异常交易警报"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "调查并识别交易模式及KYC缺陷",
      "outcomes_or_paths": [
        "发现多账户高频低额交易模式",
        "引发洗钱红旗信号",
        "意识到KYC治理和执行不足",
        "评估风险：可能暴露于金融犯罪、欺诈、监管问题并导致服务暂停"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000770",
        "quote": "CashBayou has a new head of AML compliance, Emma. On her second day on the job, she receives an alert about unusual transaction patterns. She quickly gathers her team to investigate."
      },
      {
        "unit_id": "v7u_N000771",
        "quote": "They discover that a new buyer, using multiple accounts, is making high-frequency, low-value transactions with a network of sellers who are all based in the same jurisdiction."
      },
      {
        "unit_id": "v7u_N000772",
        "quote": "This raises a red flag for money laundering."
      },
      {
        "unit_id": "v7u_N000773",
        "quote": "While investigating, Emma realizes CashBayou's current KYC governance and execution are inadequate."
      },
      {
        "unit_id": "v7u_N000774",
        "quote": "Insufficient reviews of purchasers and storefront owners could expose the platform to financia crime, fraud risks, and potential regulatory issues, which might result in temporary service suspension."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N000775",
      "v7u_N000776",
      "v7u_N000777",
      "v7u_N000778"
    ],
    "proposition": "主要支付服务商PaySecure联系CashBayou要求提供异常交易信息并召开会议，表达对政策的担忧并强调持续合作与严格监控。",
    "source_quotes": [
      "The company’s current primary payment service provider, PaySecure, which is an E-Money License Institution (EMI) registered in the UK, contacts Emma and requests more information on a series of transactions.",
      "Emma notices that the request covers part of the unusual transactions related to the new buyer.",
      "In addition, based on the frequency of transactions, PaySecure requests a cal with the compliance officer of CashBayou to understand their due diligence process.",
      "During the meeting, PaySecure expresses their concern on CashBayou’s policies and stresses the need for ongoing collaboration and rigorous monitoring to mitigate risks."
    ],
    "relation_cues": [
      "contacts",
      "requests",
      "requests a call",
      "expresses concern",
      "stresses"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "交易异常导致外部机构关注"
      ],
      "basis_or_condition": [
        "交易频率"
      ],
      "focal_handling_or_judgment": "PaySecure要求提供信息并沟通尽职调查",
      "outcomes_or_paths": [
        "表达对政策的担忧",
        "强调需要持续合作和严格监控"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000775",
        "quote": "The company’s current primary payment service provider, PaySecure, which is an E-Money License Institution (EMI) registered in the UK, contacts Emma and requests more information on a series of transactions."
      },
      {
        "unit_id": "v7u_N000776",
        "quote": "Emma notices that the request covers part of the unusual transactions related to the new buyer."
      },
      {
        "unit_id": "v7u_N000777",
        "quote": "In addition, based on the frequency of transactions, PaySecure requests a cal with the compliance officer of CashBayou to understand their due diligence process."
      },
      {
        "unit_id": "v7u_N000778",
        "quote": "During the meeting, PaySecure expresses their concern on CashBayou’s policies and stresses the need for ongoing collaboration and rigorous monitoring to mitigate risks."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N000779"
    ],
    "proposition": "发卡机构CardGuard要求CashBayou调整尽职调查程序以符合其标准，否则终止合作。",
    "source_quotes": [
      "The letter states that companies using CardGuard’s services are required to align their due diligence procedures with CardGuard’s standards for referred cardholders. Failure to comply will result in the termination of CardGuard’s partnership with CashBayou."
    ],
    "relation_cues": [
      "required to align",
      "failure to comply will result"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "CardGuard发函要求"
      ],
      "basis_or_condition": [
        "CardGuard标准"
      ],
      "focal_handling_or_judgment": "要求CashBayou调整尽职调查程序以符合标准",
      "outcomes_or_paths": [
        "符合标准则继续合作",
        "不符合则终止合作"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000779",
        "quote": "The letter states that companies using CardGuard’s services are required to align their due diligence procedures with CardGuard’s standards for referred cardholders. Failure to comply will result in the termination of CardGuard’s partnership with CashBayou."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
