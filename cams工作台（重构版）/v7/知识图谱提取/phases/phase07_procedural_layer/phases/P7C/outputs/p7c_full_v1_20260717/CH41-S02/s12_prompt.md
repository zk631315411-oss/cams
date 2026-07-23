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

section_id: `CH41-S02`

section_title: `Governance and oversight > Drafting AFC policies and procedures`

section_text_with_unit_anchors:

```text
[v7u_N002894|2894] AFC policies and procedures form the core of an organization’s AFC compliance framework, ensuring effective risk management, adherence to regulations, and operational integrity.
ZH: 金融犯罪防控政策和程序是组织合规框架的核心，确保风险管理、法规遵守和运营完整性

[v7u_N002895|2895] These policies must be clear, risk-based, and adaptable to evolving business models while aligning with global and jurisdictional AFC standards.
ZH: 金融犯罪防控政策必须清晰、基于风险、适应业务模式变化，并与全球及司法管辖区标准一致

[v7u_N002896|2896] What are AFC policies and procedures?
ZH: 引导性问题：什么是金融犯罪防控政策和程序？

[v7u_N002897|2897] Policies establish the principles, objectives, and regulatory obligations for AFC compliance. They translate legal and regulatory requirements into business-specific commitments.
ZH: 政策确立金融犯罪防控合规的原则、目标和监管义务，将法律法规转化为业务承诺

[v7u_N002898|2898] Procedures provide detailed, step-by-step implementation guidance to ensure policies are applied consistently across different business units and jurisdictions. Separate procedures are often written for a policy to tailor its execution to various business units and jurisdictions.
ZH: 程序提供详细的分步实施指南，确保政策在不同业务单元和司法管辖区一致应用

[v7u_N002899|2899] Why are AFC policies and procedures important?
ZH: 引导性问题：为什么金融犯罪防控政策和程序很重要？

[v7u_N002900|2900] Policies and procedures ensure regulatory compliance. Institutions typically choose to align their policies with FATF Recommendations, Basel Committee on Banking Supervision (BCBS) guidelines, national AML laws, and regulatory expectations.
ZH: 政策和程序确保监管合规，机构通常与FATF建议、巴塞尔委员会指南及国家反洗钱法律保持一致

[v7u_N002901|2901] Policies ensure comprehensive coverage. They should cover all products and services, including future offerings, to prevent compliance gaps.
ZH: 政策应覆盖所有产品和服务，包括未来产品，以防止合规缺口。

[v7u_N002902|2902] To follow a risk-based approach, policies must be tailored to institutional risk exposure, customer profiles, and geographic risk factors.
ZH: 基于风险的方法要求政策根据机构风险敞口、客户概况和地理风险因素量身定制。

[v7u_N002903|2903] To demonstrate proper governance and accountability, a structured policy framework ensures clear roles, responsibilities, and oversight mechanisms for compliance management.
ZH: 结构化政策框架确保合规管理中的明确角色、职责和监督机制。

[v7u_N002904|2904] Organizations should maintain a clearly defined protocol to identify when a new policy must be adopted, as well as the process for drafting, approving, and updating it.
ZH: 机构应维护明确协议，以确定何时采用新政策及其起草、批准和更新流程。

[v7u_N002905|2905] Good policies should include provisions for addressing any exceptions or exemptions and should clearly assign responsibilities to specific people or roles. They should also provide a schedule for reviewing the policy, typically on an annual basis, and stipulate events that would trigger an ad hoc review and update.
ZH: 良好政策应包括例外处理、责任分配和定期审查安排。

[v7u_N002906|2906] Examples include the introduction of a new product or the occurrence of a relevant regulatory event.
ZH: 触发临时审查的事件示例包括新产品推出或相关监管事件。

[v7u_N002907|2907] Detailed implementation guidance is provided in procedures, which are typically tailored to specific business units or other entities. In this way, changes in procedures can be made quickly to reflect changes that do not impact the entire organization.
ZH: 程序提供详细实施指南，可快速调整以适应局部变化。

[v7u_N002908|2908] How are AFC policies designed and implemented?
ZH: 关于金融犯罪防控政策设计与实施的问题引导。

[v7u_N002909|2909] Using a risk-based approach, organizations should customize policies based on customer, product, and transaction risks.
ZH: 基于风险的方法，机构应根据客户、产品和交易风险定制政策。

[v7u_N002910|2910] To ensure jurisdictional compliance, multinational organizations must align policies with country-specific laws, while maintaining global AFC principles. This may result in implementing higher standards in some jurisdictions to maintain global consistency.
ZH: 跨国机构需使政策符合各国法律，同时维持全球金融犯罪防控原则，可能需在部分司法管辖区实施更高标准。

[v7u_N002911|2911] To govern exceptions and dispensations, deviations from policy must be documented, justified, and approved by governance bodies. Where appropriate, dispensation may be provided for a specific time. Any known gaps in implementing policies must be documented and addressed within a reasonable period. A record of issues and policy violations may be centrally maintained for effective governance and oversight.
ZH: 政策偏差需记录、论证并经治理机构批准，已知实施缺口需在合理期限内解决。

[v7u_N002912|2912] When implementing new policies, organizations typically include a transition period, such as six months, to allow for:
ZH: 实施新政策时通常包含过渡期（如六个月），以便进行差距分析和业务风险评估等。

[v7u_N002913|2913] Gap analysis and business risk assessment.
ZH: 过渡期活动包括差距分析和业务风险评估。

[v7u_N002914|2914] System, procedural, and process updates
ZH: 过渡期活动包括系统、程序和流程更新。

[v7u_N002915|2915] Training and staff education.
ZH: 过渡期活动包括培训和员工教育。

[v7u_N002916|2916] By developing clear, enforceable, and adaptable AFC policies, financial institutions strengthen compliance, mitigate financial crime risks, and ensure operational resilience.
ZH: 制定清晰、可执行且适应性强的金融犯罪防控政策有助于加强合规、降低金融犯罪风险并确保运营韧性。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002904"
    ],
    "proposition": "机构应维护明确协议，以确定何时必须采用新政策，以及起草、批准和更新流程。",
    "source_quotes": [
      "Organizations should maintain a clearly defined protocol to identify when a new policy must be adopted, as well as the process for drafting, approving, and updating it."
    ],
    "relation_cues": [
      "should",
      "must",
      "as well as"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "需要采用新政策时"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "通过协议识别新政策采用时机，并执行起草、批准和更新流程",
      "outcomes_or_paths": [
        "新政策被采用或更新"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002904",
        "quote": "Organizations should maintain a clearly defined protocol to identify when a new policy must be adopted, as well as the process for drafting, approving, and updating it."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002905",
      "v7u_N002906"
    ],
    "proposition": "良好政策应包括定期审查安排（通常每年一次），并规定触发临时审查和更新的事件（如新产品或监管事件）。",
    "source_quotes": [
      "Good policies should include provisions for addressing any exceptions or exemptions and should clearly assign responsibilities to specific people or roles. They should also provide a schedule for reviewing the policy, typically on an annual basis, and stipulate events that would trigger an ad hoc review and update.",
      "Examples include the introduction of a new product or the occurrence of a relevant regulatory event."
    ],
    "relation_cues": [
      "should",
      "typically",
      "trigger",
      "examples include"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "政策需要定期审查或出现触发事件（新产品、监管事件）"
      ],
      "basis_or_condition": [
        "年度审查计划",
        "触发事件"
      ],
      "focal_handling_or_judgment": "对政策进行定期或临时审查，并视需要更新",
      "outcomes_or_paths": [
        "政策更新"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002905",
        "quote": "Good policies should include provisions for addressing any exceptions or exemptions and should clearly assign responsibilities to specific people or roles. They should also provide a schedule for reviewing the policy, typically on an annual basis, and stipulate events that would trigger an ad hoc review and update."
      },
      {
        "unit_id": "v7u_N002906",
        "quote": "Examples include the introduction of a new product or the occurrence of a relevant regulatory event."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002910"
    ],
    "proposition": "跨国机构必须使政策符合各国法律，同时维持全球金融犯罪防控原则，可能因此在部分司法管辖区实施更高标准。",
    "source_quotes": [
      "To ensure jurisdictional compliance, multinational organizations must align policies with country-specific laws, while maintaining global AFC principles. This may result in implementing higher standards in some jurisdictions to maintain global consistency."
    ],
    "relation_cues": [
      "must",
      "while",
      "may result in"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "跨国机构需要确保符合各司法管辖区法规"
      ],
      "basis_or_condition": [
        "各国法律",
        "全球金融犯罪防控原则"
      ],
      "focal_handling_or_judgment": "调整政策以符合当地法律，并维持全球原则",
      "outcomes_or_paths": [
        "可能在部分司法管辖区实施更高标准"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002910",
        "quote": "To ensure jurisdictional compliance, multinational organizations must align policies with country-specific laws, while maintaining global AFC principles. This may result in implementing higher standards in some jurisdictions to maintain global consistency."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002911"
    ],
    "proposition": "政策偏差必须记录、论证并经治理机构批准；在适当情况下可给予有时间限制的豁免。已知实施缺口需在合理期限内记录并解决。",
    "source_quotes": [
      "To govern exceptions and dispensations, deviations from policy must be documented, justified, and approved by governance bodies. Where appropriate, dispensation may be provided for a specific time. Any known gaps in implementing policies must be documented and addressed within a reasonable period."
    ],
    "relation_cues": [
      "must",
      "where appropriate",
      "may",
      "and"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "出现政策偏差或实施缺口"
      ],
      "basis_or_condition": [
        "治理机构要求"
      ],
      "focal_handling_or_judgment": "记录、论证并批准偏差，或记录并解决缺口",
      "outcomes_or_paths": [
        "偏差被批准或豁免",
        "缺口被记录并解决"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002911",
        "quote": "To govern exceptions and dispensations, deviations from policy must be documented, justified, and approved by governance bodies. Where appropriate, dispensation may be provided for a specific time. Any known gaps in implementing policies must be documented and addressed within a reasonable period."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002912",
      "v7u_N002913",
      "v7u_N002914",
      "v7u_N002915"
    ],
    "proposition": "实施新政策时通常包含过渡期（如六个月），以便进行差距分析、业务风险评估、系统/程序/流程更新以及培训。",
    "source_quotes": [
      "When implementing new policies, organizations typically include a transition period, such as six months, to allow for:",
      "Gap analysis and business risk assessment.",
      "System, procedural, and process updates",
      "Training and staff education."
    ],
    "relation_cues": [
      "When",
      "typically",
      "to allow for"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "实施新政策"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "包含过渡期（如六个月）以完成必要准备工作",
      "outcomes_or_paths": [
        "完成差距分析、业务风险评估",
        "系统/程序/流程更新",
        "培训和员工教育"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002912",
        "quote": "When implementing new policies, organizations typically include a transition period, such as six months, to allow for:"
      },
      {
        "unit_id": "v7u_N002913",
        "quote": "Gap analysis and business risk assessment."
      },
      {
        "unit_id": "v7u_N002914",
        "quote": "System, procedural, and process updates"
      },
      {
        "unit_id": "v7u_N002915",
        "quote": "Training and staff education."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
