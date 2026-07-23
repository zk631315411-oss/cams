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

section_id: `CH04-S03`

section_title: `Consequences of financial crime > Individual impact of violations of AFC regulations`

section_text_with_unit_anchors:

```text
[v7u_N000334|334] Compliance professionals are not only held accountable under financial crime laws but are also subject to all applicable criminal statutes within their jurisdiction. AML professionals can face prosecution for aiding or failing to prevent financial crimes and as seen more recently, for deficiencies in their firm's compliance program of which they carry ultimate accountability. Senior leaders, such as MLROs or BSA officers, bear the greatest personal responsibility.
ZH: 合规专业人员不仅受金融犯罪法律约束，还可能因合规缺陷面临起诉，高级领导承担最大个人责任。

[v7u_N000335|335] For example, Samantha, an MLRO, was recently investigated due to compliance failures that involved significant unreported suspicious transactions relating to financial crimes. Regulatory scrutiny identified that Samantha deliberately neglected to address compliance alerts, failed to report suspicious transactions, and inadequately documented compliance activities. Samantha faced severe consequences, including substantial regulatory fines, professional disqualification, and potential criminal charges for obstruction of justice and conspiracy.
ZH: MLRO因合规失败面临监管罚款、职业禁入和刑事指控的案例。

[v7u_N000336|336] An individual’s accountability and consequences are usually appropriate to the seniority of their role and the part they played in the non-compliance or regulatory breaches.
ZH: 个人的问责和后果通常与其职务资历及在违规中的参与程度相称。

[v7u_N000337|337] Compliance breaches made by first LoD or operational staff are more likely to result in administrative penalties or monetary fines rather than criminal prosecution, unless there is clear evidence of intentional wrongdoing or collusion.
ZH: 第一道防线或操作人员的合规违规更可能导致行政处罚或罚款，而非刑事起诉。

[v7u_N000338|338] The regulatory landscape differs across jurisdictions.
ZH: 不同司法管辖区的监管环境存在差异。

[v7u_N000339|339] For example, in many European countries severe compliance failures can lead to temporary disqualification from holding senior roles, asset freezes, or travel restrictions.
ZH: 在许多欧洲国家，严重合规失败可能导致高级职务临时禁入、资产冻结或旅行限制。

[v7u_N000340|340] US regulators are particularly stringent, and agencies like the Department of Justice and the Securities and Exchange Commission actively pursue individual accountability.
ZH: 美国监管机构尤其严格，司法部和证券交易委员会积极追究个人责任。

[v7u_N000341|341] Noncompliance with AFC regulations poses not only institutional risks but also serious, individual legal and reputational risks.
ZH: 违金融犯罪防控防控法规会带来机构和个人双重风险

[v7u_N000342|342] While all compliance professionals must adhere to rigorous standards and maintain accurate and appropriate documentation of their decision-making processes, the personal consequences for individuals in senior positions can be significantly more severe than those for more junior staff.
ZH: 高级别合规人员的个人后果比初级员工更严重
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000334",
      "v7u_N000342"
    ],
    "proposition": "合规专业人员受法律约束，高级领导承担最大个人责任，后果更严重。",
    "source_quotes": [
      "Compliance professionals are not only held accountable under financial crime laws but are also subject to all applicable criminal statutes within their jurisdiction. AML professionals can face prosecution for aiding or failing to prevent financial crimes and as seen more recently, for deficiencies in their firm's compliance program of which they carry ultimate accountability. Senior leaders, such as MLROs or BSA officers, bear the greatest personal responsibility.",
      "While all compliance professionals must adhere to rigorous standards and maintain accurate and appropriate documentation of their decision-making processes, the personal consequences for individuals in senior positions can be significantly more severe than those for more junior staff."
    ],
    "relation_cues": [
      "held accountable",
      "can face",
      "bear",
      "must",
      "can be significantly more severe"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "合规专业人员受金融犯罪法律约束"
      ],
      "basis_or_condition": [
        "高级领导角色"
      ],
      "focal_handling_or_judgment": "承担最大个人责任，可能面临起诉",
      "outcomes_or_paths": [
        "个人法律后果更严重"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000334",
        "quote": "Compliance professionals are not only held accountable under financial crime laws but are also subject to all applicable criminal statutes within their jurisdiction. AML professionals can face prosecution for aiding or failing to prevent financial crimes and as seen more recently, for deficiencies in their firm's compliance program of which they carry ultimate accountability. Senior leaders, such as MLROs or BSA officers, bear the greatest personal responsibility."
      },
      {
        "unit_id": "v7u_N000342",
        "quote": "While all compliance professionals must adhere to rigorous standards and maintain accurate and appropriate documentation of their decision-making processes, the personal consequences for individuals in senior positions can be significantly more severe than those for more junior staff."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N000335"
    ],
    "proposition": "MLRO因合规失败面临监管罚款、职业禁入和刑事指控。",
    "source_quotes": [
      "For example, Samantha, an MLRO, was recently investigated due to compliance failures that involved significant unreported suspicious transactions relating to financial crimes. Regulatory scrutiny identified that Samantha deliberately neglected to address compliance alerts, failed to report suspicious transactions, and inadequately documented compliance activities. Samantha faced severe consequences, including substantial regulatory fines, professional disqualification, and potential criminal charges for obstruction of justice and conspiracy."
    ],
    "relation_cues": [
      "due to",
      "faced",
      "including"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "合规失败：未报告可疑交易、忽视合规警报、文件记录不足"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "监管审查",
      "outcomes_or_paths": [
        "监管罚款",
        "职业禁入",
        "刑事指控（妨碍司法、共谋）"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000335",
        "quote": "For example, Samantha, an MLRO, was recently investigated due to compliance failures that involved significant unreported suspicious transactions relating to financial crimes. Regulatory scrutiny identified that Samantha deliberately neglected to address compliance alerts, failed to report suspicious transactions, and inadequately documented compliance activities. Samantha faced severe consequences, including substantial regulatory fines, professional disqualification, and potential criminal charges for obstruction of justice and conspiracy."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N000336"
    ],
    "proposition": "个人问责和后果通常与职务资历及在违规中的参与程度相称。",
    "source_quotes": [
      "An individual’s accountability and consequences are usually appropriate to the seniority of their role and the part they played in the non-compliance or regulatory breaches."
    ],
    "relation_cues": [
      "usually appropriate to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "发生违规或监管违规"
      ],
      "basis_or_condition": [
        "职务资历和参与程度"
      ],
      "focal_handling_or_judgment": "确定问责和后果",
      "outcomes_or_paths": [
        "相称的后果"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000336",
        "quote": "An individual’s accountability and consequences are usually appropriate to the seniority of their role and the part they played in the non-compliance or regulatory breaches."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N000337"
    ],
    "proposition": "第一道防线或操作人员的合规违规通常导致行政罚款而非刑事起诉，除非有故意或勾结。",
    "source_quotes": [
      "Compliance breaches made by first LoD or operational staff are more likely to result in administrative penalties or monetary fines rather than criminal prosecution, unless there is clear evidence of intentional wrongdoing or collusion."
    ],
    "relation_cues": [
      "more likely to result in",
      "rather than",
      "unless"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "合规违规"
      ],
      "basis_or_condition": [
        "第一道防线或操作人员身份",
        "无故意或勾结的推定"
      ],
      "focal_handling_or_judgment": "判定处罚类型",
      "outcomes_or_paths": [
        "通常：行政罚款",
        "有故意或勾结时：刑事起诉"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000337",
        "quote": "Compliance breaches made by first LoD or operational staff are more likely to result in administrative penalties or monetary fines rather than criminal prosecution, unless there is clear evidence of intentional wrongdoing or collusion."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N000339"
    ],
    "proposition": "在许多欧洲国家，严重合规失败可能导致临时禁入、资产冻结或旅行限制。",
    "source_quotes": [
      "For example, in many European countries severe compliance failures can lead to temporary disqualification from holding senior roles, asset freezes, or travel restrictions."
    ],
    "relation_cues": [
      "can lead to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "严重合规失败"
      ],
      "basis_or_condition": [
        "欧洲国家法律"
      ],
      "focal_handling_or_judgment": "适用处罚",
      "outcomes_or_paths": [
        "临时禁入高级职务",
        "资产冻结",
        "旅行限制"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000339",
        "quote": "For example, in many European countries severe compliance failures can lead to temporary disqualification from holding senior roles, asset freezes, or travel restrictions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N000340"
    ],
    "proposition": "美国监管机构（司法部、SEC）积极追究个人责任。",
    "source_quotes": [
      "US regulators are particularly stringent, and agencies like the Department of Justice and the Securities and Exchange Commission actively pursue individual accountability."
    ],
    "relation_cues": [
      "actively pursue"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "违反AFC法规（隐含）"
      ],
      "basis_or_condition": [
        "美国监管严格"
      ],
      "focal_handling_or_judgment": "追究个人责任",
      "outcomes_or_paths": [
        "个人法律后果（隐含）"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000340",
        "quote": "US regulators are particularly stringent, and agencies like the Department of Justice and the Securities and Exchange Commission actively pursue individual accountability."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
