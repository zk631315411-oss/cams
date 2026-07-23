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

section_id: `CH30-S01`

section_title: `Using reports, guidance notes, and policy papers in your AML/CFT controls`

section_text_with_unit_anchors:

```text
[v7u_N002151|2151] Reports, guidance notes, and policy papers vary in how they can be used for improving AML/CFT controls. Organizations take the following steps to assess the guidance from these sources and apply it to their AML/CFT controls.
ZH: 报告、指引说明和政策文件在改进反洗钱/反恐怖融资控制中的使用方式各异

[v7u_N002152|2152] Review the document in question to identify information relevant to the business’s sector, products, geography, customer base, and delivery channels.
ZH: 审查文件以识别与业务行业、产品、地域、客户群和交付渠道相关的信息

[v7u_N002153|2153] Some information in these documents might not be relevant and can be disregarded.
ZH: 文件中的某些信息可能不相关，可以忽略

[v7u_N002154|2154] Assess whether appropriate controls already exist.
ZH: 评估是否已存在适当的控制措施

[v7u_N002155|2155] For areas where appropriate controls do not exist, conduct further analysis to understand the impact of introducing such controls.
ZH: 对于缺乏适当控制的领域，进行进一步分析以了解引入控制的影响

[v7u_N002156|2156] Distinguish simple changes, with minimum business impact, from more substantial changes that could require resources to deliver, such as internal IT and product resources.
ZH: 区分简单变更（业务影响小）与需要资源（如IT和产品资源）的重大变更

[v7u_N002157|2157] Some changes can impact customer experience or have cost implications, which your organization needs to understand and plan for.
ZH: 某些变更可能影响客户体验或产生成本，组织需了解并规划

[v7u_N002158|2158] Consult with all relevant stakeholders before making a change. Ensure approval for the change from the appropriate person, such as the money laundering reporting officer. Depending on the scope and impact of the change, your organization may need to implement a communication plan and training.
ZH: 变更前需咨询利益相关方、获得适当人员批准，并可能实施沟通计划和培训

[v7u_N002159|2159] Your organization should document that it has applied information from an external report and changed its controls, policies, or procedures.
ZH: 组织应记录已应用外部报告信息并更改控制、政策或程序

[v7u_N002160|2160] Your organization can document changes to policies and procedures within the change log or elsewhere.
ZH: 组织可在变更日志或其他位置记录政策和程序的变更

[v7u_N002161|2161] This allows others, including regulators, to understand why a control exists and allows your organization to demonstrate compliance.
ZH: 合规文档有助于向监管机构证明控制措施的存在与合理性。

[v7u_N002162|2162] The enterprise-wide risk assessment (EWRA) could need adjusting to reflect newly identified risks.
ZH: 企业范围风险评估（EWRA）可能需要根据新识别的风险进行调整。

[v7u_N002163|2163] For example, imagine that a relevant authority issues a report describing a product as high risk and your organization provides this product.
ZH: 监管机构发布报告将某产品描述为高风险，而机构正提供该产品。

[v7u_N002164|2164] The EWRA should reflect this, refer to the source document, and show how your organization has applied controls to mitigate this risk.
ZH: EWRA 必须反映新风险、引用来源文件并展示控制措施。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002152"
    ],
    "proposition": "审查文件以识别与业务相关的信息。",
    "source_quotes": [
      "Review the document in question to identify information relevant to the business’s sector, products, geography, customer base, and delivery channels."
    ],
    "relation_cues": [
      "review",
      "to identify"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "审查文件以识别相关信息",
      "outcomes_or_paths": [
        "识别出与业务相关的信息"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002152",
        "quote": "Review the document in question to identify information relevant to the business’s sector, products, geography, customer base, and delivery channels."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002153"
    ],
    "proposition": "某些信息可能不相关，可以忽略。",
    "source_quotes": [
      "Some information in these documents might not be relevant and can be disregarded."
    ],
    "relation_cues": [
      "not relevant",
      "can be disregarded"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "信息可能不相关"
      ],
      "focal_handling_or_judgment": "忽略不相关信息",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002153",
        "quote": "Some information in these documents might not be relevant and can be disregarded."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002154"
    ],
    "proposition": "评估是否已存在适当的控制措施。",
    "source_quotes": [
      "Assess whether appropriate controls already exist."
    ],
    "relation_cues": [
      "assess",
      "whether"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "评估是否已存在适当控制",
      "outcomes_or_paths": [
        "确定控制存在与否"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002154",
        "quote": "Assess whether appropriate controls already exist."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002155"
    ],
    "proposition": "对于缺乏适当控制的领域，进行进一步分析以了解引入控制的影响。",
    "source_quotes": [
      "For areas where appropriate controls do not exist, conduct further analysis to understand the impact of introducing such controls."
    ],
    "relation_cues": [
      "where",
      "do not exist",
      "conduct"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "缺乏适当控制"
      ],
      "focal_handling_or_judgment": "进行进一步分析以了解引入控制的影响",
      "outcomes_or_paths": [
        "了解影响"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002155",
        "quote": "For areas where appropriate controls do not exist, conduct further analysis to understand the impact of introducing such controls."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002156"
    ],
    "proposition": "区分简单变更（业务影响小）与需要资源的重大变更。",
    "source_quotes": [
      "Distinguish simple changes, with minimum business impact, from more substantial changes that could require resources to deliver, such as internal IT and product resources."
    ],
    "relation_cues": [
      "distinguish",
      "from"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "基于业务影响和所需资源"
      ],
      "focal_handling_or_judgment": "区分简单变更与重大变更",
      "outcomes_or_paths": [
        "变更分类"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002156",
        "quote": "Distinguish simple changes, with minimum business impact, from more substantial changes that could require resources to deliver, such as internal IT and product resources."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N002157"
    ],
    "proposition": "某些变更可能影响客户体验或成本，组织需要了解并规划。",
    "source_quotes": [
      "Some changes can impact customer experience or have cost implications, which your organization needs to understand and plan for."
    ],
    "relation_cues": [
      "can impact",
      "needs to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "考虑变更影响"
      ],
      "basis_or_condition": [
        "变更可能影响客户体验或成本"
      ],
      "focal_handling_or_judgment": "了解并规划变更影响",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002157",
        "quote": "Some changes can impact customer experience or have cost implications, which your organization needs to understand and plan for."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N002158"
    ],
    "proposition": "变更前需咨询利益相关方、获得批准，并根据范围实施沟通和培训。",
    "source_quotes": [
      "Consult with all relevant stakeholders before making a change. Ensure approval for the change from the appropriate person, such as the money laundering reporting officer. Depending on the scope and impact of the change, your organization may need to implement a communication plan and training."
    ],
    "relation_cues": [
      "before",
      "ensure",
      "depending on"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "做出变更前"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "咨询利益相关方并获得批准",
      "outcomes_or_paths": [
        "实施沟通计划和培训"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002158",
        "quote": "Consult with all relevant stakeholders before making a change. Ensure approval for the change from the appropriate person, such as the money laundering reporting officer. Depending on the scope and impact of the change, your organization may need to implement a communication plan and training."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_008",
    "unit_ids": [
      "v7u_N002159",
      "v7u_N002160",
      "v7u_N002161"
    ],
    "proposition": "组织应记录应用外部报告和变更控制、政策或程序，以证明合规。",
    "source_quotes": [
      "Your organization should document that it has applied information from an external report and changed its controls, policies, or procedures.",
      "Your organization can document changes to policies and procedures within the change log or elsewhere.",
      "This allows others, including regulators, to understand why a control exists and allows your organization to demonstrate compliance."
    ],
    "relation_cues": [
      "should",
      "document",
      "allows"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "应用外部报告并更改控制"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "记录应用和变更",
      "outcomes_or_paths": [
        "证明合规"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002159",
        "quote": "Your organization should document that it has applied information from an external report and changed its controls, policies, or procedures."
      },
      {
        "unit_id": "v7u_N002160",
        "quote": "Your organization can document changes to policies and procedures within the change log or elsewhere."
      },
      {
        "unit_id": "v7u_N002161",
        "quote": "This allows others, including regulators, to understand why a control exists and allows your organization to demonstrate compliance."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_009",
    "unit_ids": [
      "v7u_N002162",
      "v7u_N002163",
      "v7u_N002164"
    ],
    "proposition": "当新风险被识别时，企业范围风险评估（EWRA）可能需要调整；例如监管报告将产品列为高风险时，EWRA应反映风险、引用来源并展示控制措施。",
    "source_quotes": [
      "The enterprise-wide risk assessment (EWRA) could need adjusting to reflect newly identified risks.",
      "For example, imagine that a relevant authority issues a report describing a product as high risk and your organization provides this product.",
      "The EWRA should reflect this, refer to the source document, and show how your organization has applied controls to mitigate this risk."
    ],
    "relation_cues": [
      "could need",
      "should",
      "reflect",
      "refer",
      "show"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "新识别风险（如监管报告将产品列为高风险）"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "调整EWRA以反映风险、引用来源并展示控制措施",
      "outcomes_or_paths": [
        "风险被反映在EWRA中"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002162",
        "quote": "The enterprise-wide risk assessment (EWRA) could need adjusting to reflect newly identified risks."
      },
      {
        "unit_id": "v7u_N002163",
        "quote": "For example, imagine that a relevant authority issues a report describing a product as high risk and your organization provides this product."
      },
      {
        "unit_id": "v7u_N002164",
        "quote": "The EWRA should reflect this, refer to the source document, and show how your organization has applied controls to mitigate this risk."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
