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

section_id: `CH34-S11`

section_title: `Three lines of defense > Liaising with internal audit`

section_text_with_unit_anchors:

```text
[v7u_N002542|2542] To prepare for audits and maintain effective control programs, AFC professionals should communicate and collaborate with their internal audit team on a regular basis. Liaising with internal audit helps to:
ZH: 金融犯罪防控专业人员应与内部审计团队定期沟通协作以准备审计。

[v7u_N002543|2543] Confirm and align review scope: Engaging with internal audit clarifies the aspects of the AFC program that will be under review and facilitates sharing of risk assessments. This ensures mutual understanding of expectations and objectives, allowing the teams to focus on the most critical areas.
ZH: 与内部审计沟通可确认并统一审查范围，确保双方理解期望与目标。

[v7u_N002544|2544] Prepare for the review: Coordinating with internal audit ensures adequate preparation. This includes gathering necessary documentation, ensuring relevant stakeholders are available, and addressing preliminary questions. Preparation minimizes disruptions and improves the audit process. For example, business practices such as regular risk and control selfassessments (RCSA) allow functions to self-identify deficiencies and implement action plans. Data from RCSA exercises also serve as valuable inputs for internal audits.
ZH: 与内部审计协调可确保充分准备，包括收集文件、安排利益相关方并处理初步问题。

[v7u_N002545|2545] Plan actions after review: After the audit, ongoing communication helps develop actionable plans in response to the results. By discussing recommendations and prioritizing actions, the AML compliance team can implement improvements promptly.
ZH: 审计后持续沟通有助于制定行动计划，反洗钱合规团队可及时实施改进。

[v7u_N002546|2546] Identify areas for improvement: A strong working relationship with internal audit fosters an environment where feedback is valued. Regular interaction helps identify areas needing improvement in compliance controls and operational processes, leading to proactive enhancements before issues escalate.
ZH: 与内部审计的良好关系有助于识别合规控制和运营流程中需要改进的领域。

[v7u_N002547|2547] Ensure effective control programs: Close collaboration with internal audit ensures that control programs function as intended.
ZH: 与内部审计密切合作可确保控制程序按预期运行。

[v7u_N002548|2548] Despite these benefits, the relationship between the compliance team and internal audit can sometimes feel adversarial.
ZH: 合规团队与内部审计之间的关系有时可能带有对抗性。

[v7u_N002549|2549] This tension arises from the built-in checks and challenges that characterize the three lines of defense model.
ZH: 这种紧张关系源于三道防线模式固有的制衡与挑战。

[v7u_N002550|2550] This structured challenge protects the organization from potential risks.
ZH: 这种结构化挑战保护组织免受潜在风险。

[v7u_N002551|2551] Understanding the different roles each line of defense plays might help alleviate some of these tensions.
ZH: 理解各道防线的不同角色有助于缓解紧张关系。

[v7u_N002552|2552] To maximize the organization’s resources and enhance control effectiveness, the three lines of defense should collaborate and coordinate. Independent tests should complement each other to provide comprehensive coverage of control programs and avoid redundancy through:
ZH: 三道防线应协作协调，独立测试应互补以避免冗余。

[v7u_N002553|2553] Joint planning sessions: Facilitating discussions among the three lines to align audit schedules, review scopes, and testing methodologies ensures that each function is aware of the others' activities and can assess different aspects of the control framework. For example, if a first-line quality assurance review is examining politically exposed persons (PEP) treatment, it might be a better use of resources for the second- and thirdline testing to focus on other high-risk areas rather than repeating the same test at the same time.
ZH: 联合规划会议可协调审计日程和范围，避免重复测试，例如对政治敏感人物的审查。

[v7u_N002554|2554] Sharing insights and findings: Open communication about audit findings helps identify identifying control gaps, enabling better analysis and remediation strategies.
ZH: 公开分享审计发现有助于识别控制缺口并制定更好的补救策略。

[v7u_N002555|2555] Leveraging expertise: Each line of defense brings unique perspectives and expertise that enhance organizational resilience.
ZH: 每道防线都带来独特的视角和专业知识，增强组织韧性。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002542",
      "v7u_N002543",
      "v7u_N002544",
      "v7u_N002545",
      "v7u_N002546",
      "v7u_N002547"
    ],
    "proposition": "金融犯罪防控专业人员应与内部审计团队定期沟通协作，以获得多方面的好处，包括确认审查范围、准备审计、制定行动计划、识别改进领域和确保控制程序有效。",
    "source_quotes": [
      "To prepare for audits and maintain effective control programs, AFC professionals should communicate and collaborate with their internal audit team on a regular basis.",
      "Confirm and align review scope: Engaging with internal audit clarifies the aspects of the AFC program that will be under review and facilitates sharing of risk assessments. This ensures mutual understanding of expectations and objectives, allowing the teams to focus on the most critical areas.",
      "Prepare for the review: Coordinating with internal audit ensures adequate preparation. This includes gathering necessary documentation, ensuring relevant stakeholders are available, and addressing preliminary questions. Preparation minimizes disruptions and improves the audit process.",
      "Plan actions after review: After the audit, ongoing communication helps develop actionable plans in response to the results. By discussing recommendations and prioritizing actions, the AML compliance team can implement improvements promptly.",
      "Identify areas for improvement: A strong working relationship with internal audit fosters an environment where feedback is valued. Regular interaction helps identify areas needing improvement in compliance controls and operational processes, leading to proactive enhancements before issues escalate.",
      "Ensure effective control programs: Close collaboration with internal audit ensures that control programs function as intended."
    ],
    "relation_cues": [
      "To",
      "should",
      "regular basis",
      "clarifies",
      "ensures",
      "helps",
      "improves",
      "fosters"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "为了准备审计和维持有效控制程序"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "与内部审计团队定期沟通协作",
      "outcomes_or_paths": [
        "确认并统一审查范围",
        "确保充分准备",
        "制定行动计划",
        "识别需要改进的领域",
        "确保控制程序有效运行"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002542",
        "quote": "To prepare for audits and maintain effective control programs, AFC professionals should communicate and collaborate with their internal audit team on a regular basis."
      },
      {
        "unit_id": "v7u_N002543",
        "quote": "Confirm and align review scope: Engaging with internal audit clarifies the aspects of the AFC program that will be under review and facilitates sharing of risk assessments. This ensures mutual understanding of expectations and objectives, allowing the teams to focus on the most critical areas."
      },
      {
        "unit_id": "v7u_N002544",
        "quote": "Prepare for the review: Coordinating with internal audit ensures adequate preparation. This includes gathering necessary documentation, ensuring relevant stakeholders are available, and addressing preliminary questions. Preparation minimizes disruptions and improves the audit process."
      },
      {
        "unit_id": "v7u_N002545",
        "quote": "Plan actions after review: After the audit, ongoing communication helps develop actionable plans in response to the results. By discussing recommendations and prioritizing actions, the AML compliance team can implement improvements promptly."
      },
      {
        "unit_id": "v7u_N002546",
        "quote": "Identify areas for improvement: A strong working relationship with internal audit fosters an environment where feedback is valued. Regular interaction helps identify areas needing improvement in compliance controls and operational processes, leading to proactive enhancements before issues escalate."
      },
      {
        "unit_id": "v7u_N002547",
        "quote": "Ensure effective control programs: Close collaboration with internal audit ensures that control programs function as intended."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002552",
      "v7u_N002553",
      "v7u_N002554",
      "v7u_N002555"
    ],
    "proposition": "三道防线应协作协调，独立测试互补，通过联合规划、分享发现和利用专长来避免冗余并增强控制有效性。",
    "source_quotes": [
      "To maximize the organization’s resources and enhance control effectiveness, the three lines of defense should collaborate and coordinate. Independent tests should complement each other to provide comprehensive coverage of control programs and avoid redundancy through:",
      "Joint planning sessions: Facilitating discussions among the three lines to align audit schedules, review scopes, and testing methodologies ensures that each function is aware of the others' activities and can assess different aspects of the control framework.",
      "Sharing insights and findings: Open communication about audit findings helps identify identifying control gaps, enabling better analysis and remediation strategies.",
      "Leveraging expertise: Each line of defense brings unique perspectives and expertise that enhance organizational resilience."
    ],
    "relation_cues": [
      "To",
      "should",
      "collaborate",
      "coordinate",
      "complement",
      "ensures",
      "helps",
      "enhance"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "为了最大化组织资源和增强控制有效性"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "三道防线协作协调，独立测试互补",
      "outcomes_or_paths": [
        "避免冗余",
        "识别控制缺口",
        "制定更好的补救策略",
        "增强组织韧性"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002552",
        "quote": "To maximize the organization’s resources and enhance control effectiveness, the three lines of defense should collaborate and coordinate. Independent tests should complement each other to provide comprehensive coverage of control programs and avoid redundancy through:"
      },
      {
        "unit_id": "v7u_N002553",
        "quote": "Joint planning sessions: Facilitating discussions among the three lines to align audit schedules, review scopes, and testing methodologies ensures that each function is aware of the others' activities and can assess different aspects of the control framework."
      },
      {
        "unit_id": "v7u_N002554",
        "quote": "Sharing insights and findings: Open communication about audit findings helps identify identifying control gaps, enabling better analysis and remediation strategies."
      },
      {
        "unit_id": "v7u_N002555",
        "quote": "Leveraging expertise: Each line of defense brings unique perspectives and expertise that enhance organizational resilience."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002548",
      "v7u_N002549",
      "v7u_N002550",
      "v7u_N002551"
    ],
    "proposition": "当合规团队与内部审计之间存在对抗性紧张关系时，理解各道防线的不同角色可能有助于缓解这些紧张关系。",
    "source_quotes": [
      "Despite these benefits, the relationship between the compliance team and internal audit can sometimes feel adversarial.",
      "This tension arises from the built-in checks and challenges that characterize the three lines of defense model.",
      "This structured challenge protects the organization from potential risks.",
      "Understanding the different roles each line of defense plays might help alleviate some of these tensions."
    ],
    "relation_cues": [
      "Despite",
      "arises from",
      "protects",
      "Understanding",
      "might help"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "合规团队与内部审计之间的关系有时可能带有对抗性"
      ],
      "basis_or_condition": [
        "三道防线模式固有的制衡与挑战"
      ],
      "focal_handling_or_judgment": "理解各道防线的不同角色",
      "outcomes_or_paths": [
        "可能有助于缓解紧张关系"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002548",
        "quote": "Despite these benefits, the relationship between the compliance team and internal audit can sometimes feel adversarial."
      },
      {
        "unit_id": "v7u_N002549",
        "quote": "This tension arises from the built-in checks and challenges that characterize the three lines of defense model."
      },
      {
        "unit_id": "v7u_N002550",
        "quote": "This structured challenge protects the organization from potential risks."
      },
      {
        "unit_id": "v7u_N002551",
        "quote": "Understanding the different roles each line of defense plays might help alleviate some of these tensions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
