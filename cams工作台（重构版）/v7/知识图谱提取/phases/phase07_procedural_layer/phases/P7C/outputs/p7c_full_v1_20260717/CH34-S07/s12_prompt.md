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

section_id: `CH34-S07`

section_title: `Three lines of defense > Compliance monitoring and testing`

section_text_with_unit_anchors:

```text
[v7u_N002472|2472] Compliance monitoring and testing assess the effectiveness of organizational processes, particularly in terms of compliance and risk management. This function is meant to ensure that policies and procedures are properly executed and continuously improved. Its primary responsibilities include reviewing the execution of policies and procedures and identifying any gaps and improvement areas across both the first and second lines.
ZH: 合规监控与测试职能评估组织流程的有效性，确保政策和程序得到正确执行并持续改进。

[v7u_N002473|2473] QA audits actions to ensure alignment with guidelines and regulatory requirements. These reviews confirm that departments follow internal controls and risk management strategies, identifying any deviations from expected practices.
ZH: 质量保证（QA）审计确保行动符合指南和监管要求，确认部门遵循内部控制与风险管理策略。

[v7u_N002474|2474] QA serves as a checks-and-balances function, seeking gaps or deficiencies in policies and procedures execution.
ZH: QA作为制衡职能，发现政策和程序执行中的差距或缺陷。

[v7u_N002475|2475] This helps mitigate risks from insufficient adherence to standards.
ZH: QA有助于缓释因标准遵循不足而产生的风险。

[v7u_N002476|2476] Through periodic assessments and audits, QA identifies trends that signify underlying issues, which may require policy adjustments or additional staff training.
ZH: QA通过定期评估和审计识别趋势，发现潜在问题，可能需要调整政策或加强培训。

[v7u_N002477|2477] QA monitors backlogs of tasks or cases that should be resolved within specific timelines. It evaluates whether these backlogs indicate process inefficiencies or resource constraints. Analyzing performance data against benchmarks allows QA to determine whether processes are effective or need reengineering to improve efficiency.
ZH: QA监控任务积压情况，评估流程效率或资源限制，分析绩效数据以确定是否需要流程再造。

[v7u_N002478|2478] QA maintains thorough documentation of audit, assessment, and review findings. This documentation serves as a compliance record and a resource for continuous improvement.
ZH: QA维护审计、评估和审查结果的详细文档，作为合规记录和持续改进的资源。

[v7u_N002479|2479] Regular reports to leadership highlight trends, compliance gaps, and corrective actions, providing decision-making information.
ZH: QA定期向领导层报告趋势、合规差距和纠正措施，提供决策信息。

[v7u_N002480|2480] QA helps identify areas needing improvement and guides the development of targeted staff training programs.
ZH: QA帮助识别需要改进的领域，并指导制定有针对性的员工培训计划。

[v7u_N002481|2481] QA promotes communication between departments on compliance issues, procedural discrepancies, and best practices. This collaborative environment enables departments to share insights and develop strategies to improve processes.
ZH: 质量保证促进部门间合规沟通与协作

[v7u_N002482|2482] QA plays a critical role in enhancing organizational integrity and efficiency. Specifically, QA functions aim to:
ZH: 质量保证在提升组织诚信与效率方面发挥关键作用，其功能旨在：

[v7u_N002483|2483] Enhance compliance: By verifying adherence to regulations and internal policies, QA helps avoid legal penalties and reputational damage.
ZH: 质量保证通过验证合规性帮助避免法律处罚和声誉损害

[v7u_N002484|2484] Improve efficiency: By identifying operational inefficiencies to streamline processes, QA optimizes resource allocation and improves service delivery.
ZH: 质量保证通过识别运营低效来优化资源配置和服务交付

[v7u_N002485|2485] Boost accountability: By introducing oversight to foster a culture of accountability. QA helps employees understand the importance of their roles within the broader context of compliance.
ZH: 质量保证通过监督促进问责文化，帮助员工理解其角色在合规中的重要性

[v7u_N002486|2486] Drive continuous improvement: The iterative nature of QA assessments supports ongoing improvements, ensuring that policies remain relevant and effective in managing emerging risks.
ZH: 质量保证的迭代评估推动持续改进，确保政策有效管理新兴风险
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002473",
      "v7u_N002474",
      "v7u_N002475"
    ],
    "proposition": "QA审计确保行动符合指南和监管要求，发现偏差，缓释风险。",
    "source_quotes": [
      "QA audits actions to ensure alignment with guidelines and regulatory requirements. These reviews confirm that departments follow internal controls and risk management strategies, identifying any deviations from expected practices.",
      "QA serves as a checks-and-balances function, seeking gaps or deficiencies in policies and procedures execution.",
      "This helps mitigate risks from insufficient adherence to standards."
    ],
    "relation_cues": [
      "audits",
      "ensure",
      "confirm",
      "identifying",
      "seeking",
      "mitigate"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "指南、监管要求、内部控制与风险管理策略"
      ],
      "focal_handling_or_judgment": "QA审计行动，确认部门遵循内控，发现偏差",
      "outcomes_or_paths": [
        "发现偏差",
        "缓释风险"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002473",
        "quote": "QA audits actions to ensure alignment with guidelines and regulatory requirements. These reviews confirm that departments follow internal controls and risk management strategies, identifying any deviations from expected practices."
      },
      {
        "unit_id": "v7u_N002474",
        "quote": "QA serves as a checks-and-balances function, seeking gaps or deficiencies in policies and procedures execution."
      },
      {
        "unit_id": "v7u_N002475",
        "quote": "This helps mitigate risks from insufficient adherence to standards."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002476"
    ],
    "proposition": "QA通过定期评估和审计识别趋势，发现潜在问题，可能需要调整政策或培训。",
    "source_quotes": [
      "Through periodic assessments and audits, QA identifies trends that signify underlying issues, which may require policy adjustments or additional staff training."
    ],
    "relation_cues": [
      "identifies",
      "may require"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "定期评估和审计"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "QA识别趋势并发现潜在问题",
      "outcomes_or_paths": [
        "可能需要调整政策或增加培训"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002476",
        "quote": "Through periodic assessments and audits, QA identifies trends that signify underlying issues, which may require policy adjustments or additional staff training."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002477"
    ],
    "proposition": "QA监控任务积压，评估流程效率或资源限制，分析绩效数据，确定是否需要流程再造。",
    "source_quotes": [
      "QA monitors backlogs of tasks or cases that should be resolved within specific timelines. It evaluates whether these backlogs indicate process inefficiencies or resource constraints. Analyzing performance data against benchmarks allows QA to determine whether processes are effective or need reengineering to improve efficiency."
    ],
    "relation_cues": [
      "monitors",
      "evaluates",
      "analyzing",
      "determine"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "任务积压"
      ],
      "basis_or_condition": [
        "绩效数据与基准"
      ],
      "focal_handling_or_judgment": "QA监控积压并评估流程效率，分析数据以判断流程有效性",
      "outcomes_or_paths": [
        "确定流程是否需要再造"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002477",
        "quote": "QA monitors backlogs of tasks or cases that should be resolved within specific timelines. It evaluates whether these backlogs indicate process inefficiencies or resource constraints. Analyzing performance data against benchmarks allows QA to determine whether processes are effective or need reengineering to improve efficiency."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002478"
    ],
    "proposition": "QA维护审计、评估和审查结果的详细文档，作为合规记录和持续改进资源。",
    "source_quotes": [
      "QA maintains thorough documentation of audit, assessment, and review findings. This documentation serves as a compliance record and a resource for continuous improvement."
    ],
    "relation_cues": [
      "maintains",
      "serves as"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "审计、评估和审查结果"
      ],
      "focal_handling_or_judgment": "QA维护详细文档",
      "outcomes_or_paths": [
        "作为合规记录和持续改进资源"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002478",
        "quote": "QA maintains thorough documentation of audit, assessment, and review findings. This documentation serves as a compliance record and a resource for continuous improvement."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002479"
    ],
    "proposition": "QA定期向领导层报告趋势、合规差距和纠正措施，提供决策信息。",
    "source_quotes": [
      "Regular reports to leadership highlight trends, compliance gaps, and corrective actions, providing decision-making information."
    ],
    "relation_cues": [
      "reports",
      "highlight",
      "providing"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "QA定期向领导层报告趋势、差距和纠正措施",
      "outcomes_or_paths": [
        "提供决策信息"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002479",
        "quote": "Regular reports to leadership highlight trends, compliance gaps, and corrective actions, providing decision-making information."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N002480"
    ],
    "proposition": "QA帮助识别需要改进的领域，并指导制定有针对性的员工培训计划。",
    "source_quotes": [
      "QA helps identify areas needing improvement and guides the development of targeted staff training programs."
    ],
    "relation_cues": [
      "identify",
      "guides"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "QA识别需要改进的领域并指导培训计划制定",
      "outcomes_or_paths": [
        "制定有针对性的培训计划"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002480",
        "quote": "QA helps identify areas needing improvement and guides the development of targeted staff training programs."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N002481"
    ],
    "proposition": "QA促进部门间合规问题、程序差异和最佳实践的沟通，形成协作环境。",
    "source_quotes": [
      "QA promotes communication between departments on compliance issues, procedural discrepancies, and best practices. This collaborative environment enables departments to share insights and develop strategies to improve processes."
    ],
    "relation_cues": [
      "promotes",
      "enables"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "合规问题、程序差异、最佳实践"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "QA促进部门间沟通",
      "outcomes_or_paths": [
        "协作环境使部门分享见解并制定改进策略"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002481",
        "quote": "QA promotes communication between departments on compliance issues, procedural discrepancies, and best practices. This collaborative environment enables departments to share insights and develop strategies to improve processes."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
