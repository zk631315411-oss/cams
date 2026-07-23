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

section_id: `CH34-S12`

section_title: `Three lines of defense > Functions of board of directors and management oversight`

section_text_with_unit_anchors:

```text
[v7u_N002556|2556] The board of directors plays a critical role in the governance and oversight of a financial institution’s AFC program. It approves the risk appetite, the scope, objectives, and responsibilities of the AFC compliance function.
ZH: 董事会在金融机构金融犯罪防控计划的治理和监督中发挥关键作用。

[v7u_N002557|2557] To demonstrate commitment to compliance and managing financial crime risks, the board must endorse the AFC program.
ZH: 董事会必须批准金融犯罪防控计划以展示对合规和风险管理的承诺。

[v7u_N002558|2558] This endorsement emphasizes AFC initiatives throughout the organization and fosters a culture of compliance.
ZH: 董事会的认可强调金融犯罪防控举措并培养合规文化。

[v7u_N002559|2559] The board should establish a dedicated AML or risk management committee with knowledgeable members to monitor implementation, review policies, and ensure adequate resources for compliance.
ZH: 董事会应设立专门的反洗钱或风险管理委员会，配备有知识的成员以监督实施和审查政策。

[v7u_N002560|2560] In addition, the board provides strategic direction for the AFC program, aligning it with the organization’s risk appetite. It assesses emerging risks and AFC control effectiveness, guiding management on any necessary adjustments. Ultimately, the board is accountable for the program's effectiveness and must ensure that any deficiencies are addressed promptly.
ZH: 董事会为金融犯罪防控计划提供战略方向，评估新兴风险，并确保及时解决缺陷。

[v7u_N002561|2561] The board and senior management play complementary roles in the effectiveness of an AFC program. Their collaboration, supported by a strong governance structure, is critical for mitigating financial crime risks and ensuring organizational integrity.
ZH: 董事会与高级管理层在金融犯罪防控中发挥互补作用

[v7u_N002562|2562] Business and operational leaders are ultimately responsible for implementing and overseeing the AFC program. They execute the program, ensure policies and procedures are integrated into operational areas, and communicate all expectations to the staff.
ZH: 业务和运营负责人负责实施和监督金融犯罪防控计划

[v7u_N002563|2563] Senior managers, often through risk management committees, are expected to monitor compliance with AFC policies and regulations.
ZH: 高级管理人员通过风险管理委员会监控金融犯罪防控合规情况

[v7u_N002564|2564] They must ensure regular reports on the program’s status, including risk assessments and any significant incidents, are submitted to the board and relevant committees.
ZH: 高级管理人员须确保向董事会定期提交金融犯罪防控计划状态报告

[v7u_N002565|2565] Management committees might review and approve reports on key performance and risk indicators, high-risk onboarding and exits, and compliance assessments, ensuring accuracy and transparency.
ZH: 管理委员会审查并批准关键绩效指标、高风险准入与退出及合规评估报告

[v7u_N002566|2566] Senior managers are responsible for any failures in the AFC program, addressing compliance deficiencies, ensuring that corrective actions are implemented, and reporting progress to the board.
ZH: 高级管理人员对金融犯罪防控计划的任何失败负责，并落实整改措施

[v7u_N002567|2567] A robust governance structure is essential for an effective AFC program.
ZH: 稳健的治理结构是有效金融犯罪防控计划的基础

[v7u_N002568|2568] Key benefits include clarity of roles and responsibilities, enhanced accountability, effective oversight and monitoring, promoting a culture of compliance, and adaptability to regulatory changes.
ZH: 稳健治理的关键益处包括职责清晰、问责增强、有效监督及合规文化
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002557",
      "v7u_N002558"
    ],
    "proposition": "为展示对合规和风险管理承诺，董事会必须批准AFC计划，这强调AFC举措并培养合规文化。",
    "source_quotes": [
      "To demonstrate commitment to compliance and managing financial crime risks, the board must endorse the AFC program.",
      "This endorsement emphasizes AFC initiatives throughout the organization and fosters a culture of compliance."
    ],
    "relation_cues": [
      "to demonstrate",
      "must",
      "emphasizes",
      "fosters"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "展示对合规和风险管理的承诺"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "董事会必须批准AFC计划",
      "outcomes_or_paths": [
        "强调AFC举措",
        "培养合规文化"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002557",
        "quote": "To demonstrate commitment to compliance and managing financial crime risks, the board must endorse the AFC program."
      },
      {
        "unit_id": "v7u_N002558",
        "quote": "This endorsement emphasizes AFC initiatives throughout the organization and fosters a culture of compliance."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002559"
    ],
    "proposition": "董事会应设立专门AML或风险管理委员会，由有知识成员组成，以监督实施、审查政策、确保资源。",
    "source_quotes": [
      "The board should establish a dedicated AML or risk management committee with knowledgeable members to monitor implementation, review policies, and ensure adequate resources for compliance."
    ],
    "relation_cues": [
      "should",
      "to monitor",
      "review",
      "ensure"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "委员会成员需有知识"
      ],
      "focal_handling_or_judgment": "董事会设立专门委员会",
      "outcomes_or_paths": [
        "监督实施",
        "审查政策",
        "确保合规资源"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002559",
        "quote": "The board should establish a dedicated AML or risk management committee with knowledgeable members to monitor implementation, review policies, and ensure adequate resources for compliance."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002560"
    ],
    "proposition": "董事会提供AFC计划战略方向，评估新兴风险和控制有效性，指导管理调整，对有效性负责并确保及时解决缺陷。",
    "source_quotes": [
      "In addition, the board provides strategic direction for the AFC program, aligning it with the organization’s risk appetite. It assesses emerging risks and AFC control effectiveness, guiding management on any necessary adjustments. Ultimately, the board is accountable for the program's effectiveness and must ensure that any deficiencies are addressed promptly."
    ],
    "relation_cues": [
      "provides",
      "assesses",
      "guiding",
      "accountable",
      "ensure"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "董事会提供战略监督并对有效性和缺陷负责",
      "outcomes_or_paths": [
        "战略方向与风险偏好对齐",
        "评估新兴风险和控制有效性",
        "指导管理调整",
        "及时解决缺陷"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002560",
        "quote": "In addition, the board provides strategic direction for the AFC program, aligning it with the organization’s risk appetite. It assesses emerging risks and AFC control effectiveness, guiding management on any necessary adjustments. Ultimately, the board is accountable for the program's effectiveness and must ensure that any deficiencies are addressed promptly."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002562"
    ],
    "proposition": "业务和运营负责人最终负责实施和监督AFC计划，执行计划，确保政策和程序融入运营，并传达期望。",
    "source_quotes": [
      "Business and operational leaders are ultimately responsible for implementing and overseeing the AFC program. They execute the program, ensure policies and procedures are integrated into operational areas, and communicate all expectations to the staff."
    ],
    "relation_cues": [
      "responsible for",
      "implementing",
      "overseeing",
      "execute",
      "ensure",
      "communicate"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "业务和运营负责人实施和监督AFC计划",
      "outcomes_or_paths": [
        "执行计划",
        "政策和程序融入运营",
        "向员工传达所有期望"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002562",
        "quote": "Business and operational leaders are ultimately responsible for implementing and overseeing the AFC program. They execute the program, ensure policies and procedures are integrated into operational areas, and communicate all expectations to the staff."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002563"
    ],
    "proposition": "高级管理人员通过风险管理委员会监控AFC政策和法规合规。",
    "source_quotes": [
      "Senior managers, often through risk management committees, are expected to monitor compliance with AFC policies and regulations."
    ],
    "relation_cues": [
      "through",
      "expected to",
      "monitor"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "通过风险管理委员会"
      ],
      "focal_handling_or_judgment": "高级管理人员监控AFC合规",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002563",
        "quote": "Senior managers, often through risk management committees, are expected to monitor compliance with AFC policies and regulations."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N002564"
    ],
    "proposition": "高级管理人员必须确保定期向董事会和相关委员会提交包括风险评估和重大事件的状态报告。",
    "source_quotes": [
      "They must ensure regular reports on the program’s status, including risk assessments and any significant incidents, are submitted to the board and relevant committees."
    ],
    "relation_cues": [
      "must",
      "ensure",
      "submitted"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "确保提交AFC计划状态报告",
      "outcomes_or_paths": [
        "报告提交给董事会和相关委员会"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002564",
        "quote": "They must ensure regular reports on the program’s status, including risk assessments and any significant incidents, are submitted to the board and relevant committees."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N002565"
    ],
    "proposition": "管理委员会可能审查和批准关键绩效指标、风险指标、高风险准入退出及合规评估报告，确保准确透明。",
    "source_quotes": [
      "Management committees might review and approve reports on key performance and risk indicators, high-risk onboarding and exits, and compliance assessments, ensuring accuracy and transparency."
    ],
    "relation_cues": [
      "might",
      "review",
      "approve",
      "ensuring"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "管理委员会审查和批准报告",
      "outcomes_or_paths": [
        "确保准确性和透明度"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002565",
        "quote": "Management committees might review and approve reports on key performance and risk indicators, high-risk onboarding and exits, and compliance assessments, ensuring accuracy and transparency."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_008",
    "unit_ids": [
      "v7u_N002566"
    ],
    "proposition": "高级管理人员对AFC计划的失败负责，处理合规缺陷，确保整改并报告进展。",
    "source_quotes": [
      "Senior managers are responsible for any failures in the AFC program, addressing compliance deficiencies, ensuring that corrective actions are implemented, and reporting progress to the board."
    ],
    "relation_cues": [
      "responsible for",
      "addressing",
      "ensuring",
      "reporting"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "高级管理人员对AFC失败负责并采取整改",
      "outcomes_or_paths": [
        "处理合规缺陷",
        "实施整改",
        "向董事会报告进展"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002566",
        "quote": "Senior managers are responsible for any failures in the AFC program, addressing compliance deficiencies, ensuring that corrective actions are implemented, and reporting progress to the board."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
