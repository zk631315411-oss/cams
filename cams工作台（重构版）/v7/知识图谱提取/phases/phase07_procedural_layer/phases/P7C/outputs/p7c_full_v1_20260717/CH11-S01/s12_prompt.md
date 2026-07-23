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

section_id: `CH11-S01`

section_title: `Money laundering risks associated with MSBs, payment service providers, and ecommerce > Payment service providers`

section_text_with_unit_anchors:

```text
[v7u_N000781|781] The payment industry and associated technologies are evolving rapidly, often outpacing the development of licensing frameworks and regulatory oversight. In this dynamic environment, many organizations leverage money services business (MSB) or e-money licenses to expand their operations and carve out a distinct role within the broader payments ecosystem.
ZH: 支付行业快速发展，企业利用货币服务企业或电子货币牌照拓展业务

[v7u_N000782|782] Payment service providers (PSP) play a central role, by enabling digital payments across various industries, offering products and services tailored to their business models and the types of transactions they process.
ZH: 支付服务提供商（PSP）在数字支付中发挥核心作用

[v7u_N000783|783] These services can include payment aggregation, card issuance, mobile wallets, and cross-border payment facilitation.
ZH: PSP服务包括支付聚合、卡片发行、移动钱包和跨境支付

[v7u_N000784|784] In some financial institutions, MSBs and PSPs are collectively referred to as “Third-Party Payment Processors” (TPPP), reflecting their shared function of handling transactions on behalf of other entities.
ZH: 货币服务企业和PSP统称为第三方支付处理商（TPPP）

[v7u_N000785|785] A typical PSP flow that facilitates the processing of a payment transaction between a customer and a merchant includes:
ZH: 典型PSP处理客户与商户间支付交易的流程

[v7u_N000786|786] 1. Verification: The PSP verifies the customer’s payment information with the issuing bank.
ZH: PSP验证客户支付信息与发卡行

[v7u_N000787|787] 2. Approval: The PSP communicates with the issuing bank to receive approval for the transaction.
ZH: PSP与发卡行沟通获取交易批准

[v7u_N000788|788] 3. Transfer: The PSP transfers funds from the customer’s account to the business’s account.
ZH: PSP将资金从客户账户转入商户账户

[v7u_N000789|789] Services include online payment gateways, mobile wallet solutions, and crossborder payment systems.
ZH: PSP服务包括在线支付网关、移动钱包和跨境支付系统

[v7u_N000790|790] A payment gateway is vital for processing payments because it facilitates the actual transfer of funds.
ZH: 支付网关是处理资金转移的关键

[v7u_N000791|791] As demand for digital solutions grows, PSPs are expected to expand product offerings, adapt to customer needs, and comply with changing regulations. This adaptability ensures they stay at the forefront of the payment landscape.
ZH: PSP需扩展产品、适应客户需求并遵守法规以保持领先

[v7u_N000792|792] Examples of PSPs and their offerings:
ZH: PSP及其产品示例列表

[v7u_N000793|793] Managing risks is essential for PSPs due to the complexity and diversity of their services, and because most transactions are conducted remotely.
ZH: 由于服务复杂多样且远程交易，PSP必须进行风险管理

[v7u_N000794|794] The risk landscape for PSPs varies based on their specific product offerings. However, key risks include:
ZH: PSP风险状况因产品而异，关键风险包括

[v7u_N000795|795] Fraud: The potential for deceptive practices that can lead to financial loss.
ZH: 欺诈：可能导致财务损失的欺骗行为

[v7u_N000796|796] Chargebacks: Disputes initiated by customers that can impact revenue.
ZH: 退单：客户发起的争议，影响收入

[v7u_N000797|797] Data breaches: Unauthorized access to sensitive customer information.
ZH: 数据泄露：未经授权访问敏感客户信息

[v7u_N000798|798] Regulatory noncompliance: Risks associated with failing to adhere to legal requirements.
ZH: 监管不合规：未遵守法律要求的风险

[v7u_N000799|799] Operational failures: Disruptions in service delivery that can affect business operations.
ZH: 运营故障：服务交付中断影响业务运营

[v7u_N000800|800] Financial losses: Overall impact on profitability due to various risk factors.
ZH: 财务损失：各种风险因素对盈利能力的整体影响

[v7u_N000801|801] For PSPs, customer risks are primarily indirect.
ZH: 支付服务商的客户风险主要是间接风险

[v7u_N000802|802] Although PSPs usually do not directly engage in the financial or transactional activities of their customers, they still bear the responsibility of ensuring that transactions and AFC program controls comply with regulations. This includes confirming that these transactions are secure and do not lead to financial crimes.
ZH: 支付服务商有责任确保交易合规与安全，防止金融犯罪

[v7u_N000803|803] In contrast, partnership risks are typically higher due to PSPs' operational reliance on banks, financial institutions, card networks, technology providers, and third-party service providers.
ZH: 支付服务商的合作风险通常更高，因其依赖银行、金融机构等合作伙伴

[v7u_N000804|804] It is important for PSPs to understand their partners’ AFC controls in order to mitigate the relevant risks.
ZH: 支付服务商必须了解合作伙伴的金融犯罪防控措施以降低风险

[v7u_N000805|805] One concern is regulatory compliance risk.
ZH: 监管合规风险是支付服务商面临的一个担忧

[v7u_N000806|806] PSPs must ensure that their partners adhere to regulations and data protection requirements, such as the EU’s Payment Services Directive for strong customer authentication.
ZH: 支付服务商必须确保合作伙伴遵守法规和数据保护要求

[v7u_N000807|807] Their noncompliance can lead to repercussions for PSPs because noncompliant partners might inadvertently facilitate money laundering by creating gaps in the controls to detect illicit activities.
ZH: 不合规的合作伙伴可能在控制措施中留下漏洞，无意中助长洗钱

[v7u_N000808|808] Operational risks also present challenges, as many PSPs depend on thirdparty providers for essential infrastructure, including cloud storage.
ZH: 支付服务商依赖第三方提供商提供云存储等关键基础设施，带来运营风险

[v7u_N000809|809] Service outages and issues, such as long response times or inadequate customer support, are red flags, as they might indicate lapses in the partner’s transaction monitoring and compliance efforts.
ZH: 服务中断、响应时间长或客服不足是合作伙伴合规松懈的红旗信号信号

[v7u_N000810|810] Cybersecurity and fraud risks are heightened when collaborating with various institutions.
ZH: 与不同机构合作时，网络安全和欺诈风险会升高

[v7u_N000811|811] Differences in cybersecurity standards can create integration gaps, and in the event of a breach, the PSP is often responsible for customer communication and damage control.
ZH: 网络安全标准差异造成融合阶段缺口，发生泄露时支付服务商常需负责客户沟通与损害控制

[v7u_N000812|812] A partner's failure to maintain robust cybersecurity measures can lead to unauthorized access to sensitive data, facilitating fraudulent activities and money laundering.
ZH: 合作伙伴网络安全措施不力可导致敏感数据被未授权访问，助长欺诈和洗钱
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000801",
      "v7u_N000802"
    ],
    "proposition": "支付服务商的客户风险主要是间接风险；尽管支付服务商通常不直接参与客户的金融或交易活动，但他们仍有责任确保交易和反金融犯罪控制合规。",
    "source_quotes": [
      "For PSPs, customer risks are primarily indirect.",
      "Although PSPs usually do not directly engage in the financial or transactional activities of their customers, they still bear the responsibility of ensuring that transactions and AFC program controls comply with regulations."
    ],
    "relation_cues": [
      "primarily",
      "indirect",
      "Although",
      "still bear the responsibility"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "PSP通常不直接参与客户的金融或交易活动"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "PSP负有确保交易和反金融犯罪控制合规的责任",
      "outcomes_or_paths": [
        "确保交易安全，防止金融犯罪"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000801",
        "quote": "For PSPs, customer risks are primarily indirect."
      },
      {
        "unit_id": "v7u_N000802",
        "quote": "Although PSPs usually do not directly engage in the financial or transactional activities of their customers, they still bear the responsibility of ensuring that transactions and AFC program controls comply with regulations."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N000803",
      "v7u_N000804"
    ],
    "proposition": "支付服务商的合作风险通常更高，因依赖银行等合作伙伴；支付服务商必须了解合作伙伴的反金融犯罪控制以降低相关风险。",
    "source_quotes": [
      "In contrast, partnership risks are typically higher due to PSPs' operational reliance on banks, financial institutions, card networks, technology providers, and third-party service providers.",
      "It is important for PSPs to understand their partners’ AFC controls in order to mitigate the relevant risks."
    ],
    "relation_cues": [
      "In contrast",
      "typically higher",
      "due to",
      "it is important",
      "in order to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "PSP运营依赖银行、金融机构、卡网络、技术提供商和第三方服务商"
      ],
      "basis_or_condition": [
        "合作风险通常更高"
      ],
      "focal_handling_or_judgment": "PSP必须了解合作伙伴的反金融犯罪控制",
      "outcomes_or_paths": [
        "降低相关风险"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000803",
        "quote": "In contrast, partnership risks are typically higher due to PSPs' operational reliance on banks, financial institutions, card networks, technology providers, and third-party service providers."
      },
      {
        "unit_id": "v7u_N000804",
        "quote": "It is important for PSPs to understand their partners’ AFC controls in order to mitigate the relevant risks."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N000805",
      "v7u_N000806"
    ],
    "proposition": "监管合规风险是支付服务商的担忧；支付服务商必须确保其合作伙伴遵守法规和数据保护要求，例如欧盟支付服务指令中的强客户认证。",
    "source_quotes": [
      "One concern is regulatory compliance risk.",
      "PSPs must ensure that their partners adhere to regulations and data protection requirements, such as the EU’s Payment Services Directive for strong customer authentication."
    ],
    "relation_cues": [
      "concern",
      "must ensure",
      "such as"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "监管合规风险"
      ],
      "basis_or_condition": [
        "欧盟支付服务指令等法规和数据保护要求"
      ],
      "focal_handling_or_judgment": "PSP必须确保合作伙伴遵守法规和数据保护要求",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000805",
        "quote": "One concern is regulatory compliance risk."
      },
      {
        "unit_id": "v7u_N000806",
        "quote": "PSPs must ensure that their partners adhere to regulations and data protection requirements, such as the EU’s Payment Services Directive for strong customer authentication."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N000809"
    ],
    "proposition": "服务中断、响应时间长或客服不足是红旗信号，可能表明合作伙伴的交易监控和合规工作存在疏漏。",
    "source_quotes": [
      "Service outages and issues, such as long response times or inadequate customer support, are red flags, as they might indicate lapses in the partner’s transaction monitoring and compliance efforts."
    ],
    "relation_cues": [
      "are red flags",
      "as",
      "might indicate"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "服务中断、响应时间长或客服不足"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "判断合作伙伴的交易监控和合规工作存在疏漏",
      "outcomes_or_paths": [
        "被识别为红旗信号"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000809",
        "quote": "Service outages and issues, such as long response times or inadequate customer support, are red flags, as they might indicate lapses in the partner’s transaction monitoring and compliance efforts."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N000810",
      "v7u_N000811"
    ],
    "proposition": "与不同机构合作时，网络安全和欺诈风险升高；发生泄露时，支付服务商通常负责客户沟通与损害控制。",
    "source_quotes": [
      "Cybersecurity and fraud risks are heightened when collaborating with various institutions.",
      "Differences in cybersecurity standards can create integration gaps, and in the event of a breach, the PSP is often responsible for customer communication and damage control."
    ],
    "relation_cues": [
      "heightened",
      "when",
      "in the event of",
      "often responsible"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "与不同机构合作",
        "发生泄露"
      ],
      "basis_or_condition": [
        "网络安全标准差异造成融合缺口"
      ],
      "focal_handling_or_judgment": "PSP负责客户沟通与损害控制",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000810",
        "quote": "Cybersecurity and fraud risks are heightened when collaborating with various institutions."
      },
      {
        "unit_id": "v7u_N000811",
        "quote": "Differences in cybersecurity standards can create integration gaps, and in the event of a breach, the PSP is often responsible for customer communication and damage control."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
