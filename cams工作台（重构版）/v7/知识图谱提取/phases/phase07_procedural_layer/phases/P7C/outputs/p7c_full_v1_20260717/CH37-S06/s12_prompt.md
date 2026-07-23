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

section_id: `CH37-S06`

section_title: `Enterprise-wide risk assessment > Reporting results of risk assessment`

section_text_with_unit_anchors:

```text
[v7u_N002808|2808] While risk assessments are critical to evaluating the health of a financial institution’s compliance programs, it is equally important to report the information to senior management and other stakeholders.
ZH: 风险评估结果必须报告给高级管理层和其他利益相关者。

[v7u_N002809|2809] They need to review the report comprehensively to understand its meaning. Their efforts include reviewing whether risk levels have remained the same, decreased, or increased. These stakeholders are also responsible for using the report to ask questions, or even to challenge an organization’s compliance programs.
ZH: 利益相关者需全面审阅报告，理解其含义，检查风险水平变化，并利用报告提问或质疑合规计划。

[v7u_N002810|2810] The results of the risk assessment, and feedback from senior management, have an impact on policies, procedures, systems, resources, staffing, and training.
ZH: 风险评估结果及高级管理层反馈会影响政策、程序、系统、资源、人员配置和培训。

[v7u_N002811|2811] Risk assessments are vital for organizations to understand their unique risk profiles.
ZH: 风险评估对于机构了解其独特风险状况至关重要。

[v7u_N002812|2812] However, the true value of an end-to-end risk assessment depends on its outcomes.
ZH: 端到端风险评估的真正价值取决于其成果。

[v7u_N002813|2813] To determine where changes need to be made, all stakeholders from an institution need to review and discuss the risk assessment’s outcomes. This includes senior management, compliance and operational branches, business lines, and internal auditing.
ZH: 所有利益相关者（高级管理层、合规与运营部门、业务条线、内部审计）必须审阅并讨论风险评估成果。

[v7u_N002814|2814] Risk assessment teams have three main reporting responsibilities:
ZH: 风险评估团队有三项主要报告职责。

[v7u_N002815|2815] Present the report, its methodology, and supporting data to stakeholders.
ZH: 向利益相关者提交报告、方法论和支持数据。

[v7u_N002816|2816] Ensure the report and its supporting data are clear and understandable.
ZH: 确保报告及其支持数据清晰易懂。

[v7u_N002817|2817] Respond to questions and challenges from stakeholders about methodology, procedures, data, and outcomes of the report.
ZH: 回应利益相关者对报告方法论、程序、数据和成果的提问与质疑。

[v7u_N002818|2818] This process aids an organization’s ongoing AFC efforts because it identifies where risks are weak or strong.
ZH: 该过程通过识别风险强弱，支持机构的持续金融犯罪防控（金融犯罪防控）工作。

[v7u_N002819|2819] Risk assessment reporting should be more than an administrative exercise.
ZH: 风险评估报告不应仅是行政性工作。

[v7u_N002820|2820] The risk assessment should identify clients, products, and services that might exceed the organization’s risk appetite.
ZH: 风险评估应识别可能超出机构风险偏好的客户、产品和服务。

[v7u_N002821|2821] A good risk assessment report will also recommend compensating control enhancements, which include new controls or enhanced existing controls to compensate for any weaknesses.
ZH: 良好的风险评估报告会推荐补偿性控制增强措施以弥补弱点

[v7u_N002822|2822] Senior management can meaningfully utilize the report to determine where to attribute staffing, resources, technology, and training to further mitigate risk.
ZH: 高级管理层应利用风险评估报告决定人员、资源、技术和培训的配置以进一步降低风险
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002808"
    ],
    "proposition": "风险评估结果必须报告给高级管理层和其他利益相关者。",
    "source_quotes": [
      "While risk assessments are critical to evaluating the health of a financial institution’s compliance programs, it is equally important to report the information to senior management and other stakeholders."
    ],
    "relation_cues": [
      "while",
      "report"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "风险评估完成"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "向高级管理层和其他利益相关者报告风险评估信息",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002808",
        "quote": "While risk assessments are critical to evaluating the health of a financial institution’s compliance programs, it is equally important to report the information to senior management and other stakeholders."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002809"
    ],
    "proposition": "利益相关者需全面审阅报告，理解其含义，检查风险水平变化，并利用报告提问或质疑合规计划。",
    "source_quotes": [
      "They need to review the report comprehensively to understand its meaning. Their efforts include reviewing whether risk levels have remained the same, decreased, or increased. These stakeholders are also responsible for using the report to ask questions, or even to challenge an organization’s compliance programs."
    ],
    "relation_cues": [
      "need to",
      "include",
      "responsible for"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "收到风险评估报告"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "利益相关者审阅报告、理解含义、检查风险水平变化、提问或质疑合规计划",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002809",
        "quote": "They need to review the report comprehensively to understand its meaning. Their efforts include reviewing whether risk levels have remained the same, decreased, or increased. These stakeholders are also responsible for using the report to ask questions, or even to challenge an organization’s compliance programs."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002810"
    ],
    "proposition": "风险评估结果及高级管理层反馈会影响政策、程序、系统、资源、人员配置和培训。",
    "source_quotes": [
      "The results of the risk assessment, and feedback from senior management, have an impact on policies, procedures, systems, resources, staffing, and training."
    ],
    "relation_cues": [
      "have an impact on"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "风险评估结果和高级管理层反馈"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "影响政策、程序、系统、资源、人员配置和培训",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002810",
        "quote": "The results of the risk assessment, and feedback from senior management, have an impact on policies, procedures, systems, resources, staffing, and training."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002813"
    ],
    "proposition": "所有利益相关者（高级管理层、合规与运营部门、业务条线、内部审计）必须审阅并讨论风险评估成果，以确定需要改变的地方。",
    "source_quotes": [
      "To determine where changes need to be made, all stakeholders from an institution need to review and discuss the risk assessment’s outcomes. This includes senior management, compliance and operational branches, business lines, and internal auditing."
    ],
    "relation_cues": [
      "to determine",
      "need to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "确定需要改变的地方"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "所有利益相关者审阅并讨论风险评估成果",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002813",
        "quote": "To determine where changes need to be made, all stakeholders from an institution need to review and discuss the risk assessment’s outcomes. This includes senior management, compliance and operational branches, business lines, and internal auditing."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002814",
      "v7u_N002815",
      "v7u_N002816",
      "v7u_N002817"
    ],
    "proposition": "风险评估团队有三个主要报告职责：向利益相关者提交报告、确保报告清晰易懂、回应问题。",
    "source_quotes": [
      "Risk assessment teams have three main reporting responsibilities:",
      "Present the report, its methodology, and supporting data to stakeholders.",
      "Ensure the report and its supporting data are clear and understandable.",
      "Respond to questions and challenges from stakeholders about methodology, procedures, data, and outcomes of the report."
    ],
    "relation_cues": [
      "responsibilities",
      "present",
      "ensure",
      "respond"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "风险评估完成"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "履行报告职责：提交报告、确保清晰、回应问题",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002814",
        "quote": "Risk assessment teams have three main reporting responsibilities:"
      },
      {
        "unit_id": "v7u_N002815",
        "quote": "Present the report, its methodology, and supporting data to stakeholders."
      },
      {
        "unit_id": "v7u_N002816",
        "quote": "Ensure the report and its supporting data are clear and understandable."
      },
      {
        "unit_id": "v7u_N002817",
        "quote": "Respond to questions and challenges from stakeholders about methodology, procedures, data, and outcomes of the report."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N002818"
    ],
    "proposition": "报告过程通过识别风险强弱，支持机构的持续金融犯罪防控工作。",
    "source_quotes": [
      "This process aids an organization’s ongoing AFC efforts because it identifies where risks are weak or strong."
    ],
    "relation_cues": [
      "aids",
      "because",
      "identifies"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "报告过程"
      ],
      "basis_or_condition": [
        "识别风险弱项和强项"
      ],
      "focal_handling_or_judgment": "识别风险弱项和强项",
      "outcomes_or_paths": [
        "支持机构的持续金融犯罪防控工作"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002818",
        "quote": "This process aids an organization’s ongoing AFC efforts because it identifies where risks are weak or strong."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N002820"
    ],
    "proposition": "风险评估应识别可能超出机构风险偏好的客户、产品和服务。",
    "source_quotes": [
      "The risk assessment should identify clients, products, and services that might exceed the organization’s risk appetite."
    ],
    "relation_cues": [
      "should",
      "identify",
      "exceed"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "风险评估过程"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "识别可能超出风险偏好的客户、产品和服务",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002820",
        "quote": "The risk assessment should identify clients, products, and services that might exceed the organization’s risk appetite."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_008",
    "unit_ids": [
      "v7u_N002821"
    ],
    "proposition": "良好的风险评估报告会推荐补偿性控制增强措施，包括新控制或强化现有控制以弥补弱点。",
    "source_quotes": [
      "A good risk assessment report will also recommend compensating control enhancements, which include new controls or enhanced existing controls to compensate for any weaknesses."
    ],
    "relation_cues": [
      "recommend",
      "include",
      "compensate for"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "发现弱点"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "推荐补偿性控制增强措施",
      "outcomes_or_paths": [
        "新控制或强化现有控制以弥补弱点"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002821",
        "quote": "A good risk assessment report will also recommend compensating control enhancements, which include new controls or enhanced existing controls to compensate for any weaknesses."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_009",
    "unit_ids": [
      "v7u_N002822"
    ],
    "proposition": "高级管理层可利用风险评估报告决定人员、资源、技术和培训的配置以进一步降低风险。",
    "source_quotes": [
      "Senior management can meaningfully utilize the report to determine where to attribute staffing, resources, technology, and training to further mitigate risk."
    ],
    "relation_cues": [
      "utilize",
      "determine",
      "mitigate"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "收到风险评估报告"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "利用报告决定资源分配以降低风险",
      "outcomes_or_paths": [
        "进一步降低风险"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002822",
        "quote": "Senior management can meaningfully utilize the report to determine where to attribute staffing, resources, technology, and training to further mitigate risk."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
