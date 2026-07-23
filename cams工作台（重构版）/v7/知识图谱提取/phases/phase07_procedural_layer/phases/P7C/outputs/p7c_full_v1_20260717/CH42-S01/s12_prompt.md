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

section_id: `CH42-S01`

section_title: `Onboarding AFC controls > The KYC process`

section_text_with_unit_anchors:

```text
[v7u_N003011|3011] With evolving global regulatory frameworks, financial institutions must implement risk-based due diligence to prevent financial crime.
ZH: 金融机构必须实施基于风险的尽职调查以防止金融犯罪

[v7u_N003012|3012] The KYC process is a core requirement in AFC compliance, ensuring financial institutions identify, verify, and assess customer risks before establishing or maintaining business relationships.
ZH: 了解你的客户流程是金融犯罪合规的核心要求，用于识别、验证和评估客户风险

[v7u_N003013|3013] For specific customer profiles, such as PEPs, high-net-worth individuals, and customers from high-risk jurisdictions, a pre-KYC onboarding committee might assess suitability before formal identification.
ZH: 对于政治敏感人物等特定客户，在正式了解你的客户前由委员会评估其适宜性

[v7u_N003014|3014] The committee typically includes compliance experts, risk managers, legal advisors, and business unit leaders, who collectively evaluate jurisdictional risks, business activities, and strategic fit.
ZH: 委员会由合规、风险、法务及业务部门代表组成，评估司法管辖区风险等

[v7u_N003015|3015] The outcome determines whether customers proceed to full KYC and what level of due diligence—standard or enhanced—is required.
ZH: 委员会评估结果决定客户是否进入完整了解你的客户及所需尽职调查级别

[v7u_N003016|3016] This step ensures efficient resource use, early risk mitigation, and regulatory alignment by filtering out unsuitable clients early in the process.
ZH: 了解你的客户前步骤旨在早期过滤不合适客户，确保资源高效利用和监管合规

[v7u_N003017|3017] The typical KYC/CDD process consists of the following steps:
ZH: 典型的了解你的客户/客户尽职调查流程包含以下步骤

[v7u_N003018|3018] Identity and verification (ID&V):
ZH: 身份识别与验证步骤

[v7u_N003019|3019] Identification is the collection of personal and business details, including name, date of birth, nationality, address, tax identification number, and company registration data.
ZH: 身份识别是收集个人和企业的详细信息

[v7u_N003020|3020] Verification is the authentication of provided information using government-issued documents, biometric authentication, AI-driven verification tools, and forensic analysis of identification records.
ZH: 验证是通过政府文件、生物识别等技术对信息进行认证

[v7u_N003021|3021] Organizations must understand and obtain information, as appropriate, on the purpose and intended nature of the customer’s relationship with the organization.
ZH: 机构必须了解客户关系的预期目的和性质

[v7u_N003022|3022] Enhanced regulations require organizations to determine the ultimate beneficial owners (UBOs) of corporate accounts.
ZH: 强化法规要求机构确定公司账户的最终受益所有人

[v7u_N003023|3023] Screening is conducted prior to onboarding to determine risk:
ZH: 在客户准入前进行筛查以确定风险

[v7u_N003024|3024] Sanctions screening is when customer details are cross-checked against UN, EU, OFAC, and national sanctions lists to detect high-risk entities.
ZH: 制裁筛查是将客户信息与联合国、欧盟、OFAC及国家制裁名单进行交叉核对

[v7u_N003025|3025] Adverse media monitoring is conducted to identify links to financial crime, corruption, and fraudulent activities.
ZH: 负面媒体监控旨在识别与金融犯罪、腐败和欺诈活动的关联

[v7u_N003026|3026] PEP screening is when organizations determine whether the individual or beneficial owner is a PEP, or the relative or close associate of a PEP.
ZH: 政治敏感人物筛查用于确定个人或受益所有人是否为政治敏感人物或其亲属或密切关联人
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N003013",
      "v7u_N003014",
      "v7u_N003015",
      "v7u_N003016"
    ],
    "proposition": "对于政治敏感人物等特定客户，在正式KYC前由委员会评估其适宜性，决定是否进入完整KYC及所需尽职调查级别。",
    "source_quotes": [
      "For specific customer profiles, such as PEPs, high-net-worth individuals, and customers from high-risk jurisdictions, a pre-KYC onboarding committee might assess suitability before formal identification.",
      "The committee typically includes compliance experts, risk managers, legal advisors, and business unit leaders, who collectively evaluate jurisdictional risks, business activities, and strategic fit.",
      "The outcome determines whether customers proceed to full KYC and what level of due diligence—standard or enhanced—is required.",
      "This step ensures efficient resource use, early risk mitigation, and regulatory alignment by filtering out unsuitable clients early in the process."
    ],
    "relation_cues": [
      "might assess",
      "determines",
      "filtering out"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "特定客户：政治敏感人物、高净值人士、高风险司法管辖区客户"
      ],
      "basis_or_condition": [
        "委员会评估司法管辖区风险、业务活动及战略契合度"
      ],
      "focal_handling_or_judgment": "委员会评估客户适宜性",
      "outcomes_or_paths": [
        "客户可进入完整KYC并确定尽职调查级别（标准或强化）",
        "或客户被过滤掉"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N003013",
        "quote": "For specific customer profiles, such as PEPs, high-net-worth individuals, and customers from high-risk jurisdictions, a pre-KYC onboarding committee might assess suitability before formal identification."
      },
      {
        "unit_id": "v7u_N003014",
        "quote": "The committee typically includes compliance experts, risk managers, legal advisors, and business unit leaders, who collectively evaluate jurisdictional risks, business activities, and strategic fit."
      },
      {
        "unit_id": "v7u_N003015",
        "quote": "The outcome determines whether customers proceed to full KYC and what level of due diligence—standard or enhanced—is required."
      },
      {
        "unit_id": "v7u_N003016",
        "quote": "This step ensures efficient resource use, early risk mitigation, and regulatory alignment by filtering out unsuitable clients early in the process."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N003018",
      "v7u_N003019",
      "v7u_N003020",
      "v7u_N003021",
      "v7u_N003022"
    ],
    "proposition": "身份识别与验证（ID&V）包括收集个人和业务信息、验证文件、了解业务目的、确定最终受益所有人。",
    "source_quotes": [
      "Identity and verification (ID&V):",
      "Identification is the collection of personal and business details, including name, date of birth, nationality, address, tax identification number, and company registration data.",
      "Verification is the authentication of provided information using government-issued documents, biometric authentication, AI-driven verification tools, and forensic analysis of identification records.",
      "Organizations must understand and obtain information, as appropriate, on the purpose and intended nature of the customer’s relationship with the organization.",
      "Enhanced regulations require organizations to determine the ultimate beneficial owners (UBOs) of corporate accounts."
    ],
    "relation_cues": [
      "must understand",
      "require",
      "is"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "KYC流程中的身份识别与验证步骤"
      ],
      "basis_or_condition": [
        "收集信息、验证文件、了解业务目的、识别UBO"
      ],
      "focal_handling_or_judgment": "身份识别与验证（ID&V）",
      "outcomes_or_paths": [
        "获取客户身份信息并验证"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N003018",
        "quote": "Identity and verification (ID&V):"
      },
      {
        "unit_id": "v7u_N003019",
        "quote": "Identification is the collection of personal and business details, including name, date of birth, nationality, address, tax identification number, and company registration data."
      },
      {
        "unit_id": "v7u_N003020",
        "quote": "Verification is the authentication of provided information using government-issued documents, biometric authentication, AI-driven verification tools, and forensic analysis of identification records."
      },
      {
        "unit_id": "v7u_N003021",
        "quote": "Organizations must understand and obtain information, as appropriate, on the purpose and intended nature of the customer’s relationship with the organization."
      },
      {
        "unit_id": "v7u_N003022",
        "quote": "Enhanced regulations require organizations to determine the ultimate beneficial owners (UBOs) of corporate accounts."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N003023",
      "v7u_N003024",
      "v7u_N003025",
      "v7u_N003026"
    ],
    "proposition": "在客户准入前进行筛查以确定风险，包括制裁筛查、负面媒体监控和PEP筛查。",
    "source_quotes": [
      "Screening is conducted prior to onboarding to determine risk:",
      "Sanctions screening is when customer details are cross-checked against UN, EU, OFAC, and national sanctions lists to detect high-risk entities.",
      "Adverse media monitoring is conducted to identify links to financial crime, corruption, and fraudulent activities.",
      "PEP screening is when organizations determine whether the individual or beneficial owner is a PEP, or the relative or close associate of a PEP."
    ],
    "relation_cues": [
      "conducted to determine",
      "cross-checked",
      "identify"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "客户准入前"
      ],
      "basis_or_condition": [
        "制裁名单、负面媒体、PEP标准"
      ],
      "focal_handling_or_judgment": "筛查以确定风险",
      "outcomes_or_paths": [
        "识别高风险实体、关联金融犯罪或腐败、识别PEP身份"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N003023",
        "quote": "Screening is conducted prior to onboarding to determine risk:"
      },
      {
        "unit_id": "v7u_N003024",
        "quote": "Sanctions screening is when customer details are cross-checked against UN, EU, OFAC, and national sanctions lists to detect high-risk entities."
      },
      {
        "unit_id": "v7u_N003025",
        "quote": "Adverse media monitoring is conducted to identify links to financial crime, corruption, and fraudulent activities."
      },
      {
        "unit_id": "v7u_N003026",
        "quote": "PEP screening is when organizations determine whether the individual or beneficial owner is a PEP, or the relative or close associate of a PEP."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
