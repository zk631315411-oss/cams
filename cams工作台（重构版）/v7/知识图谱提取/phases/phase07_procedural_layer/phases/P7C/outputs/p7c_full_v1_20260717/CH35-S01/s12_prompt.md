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

section_id: `CH35-S01`

section_title: `Second LOD's AFC role and its interaction with the front office`

section_text_with_unit_anchors:

```text
[v7u_N002569|2569] The second line of defense (LOD) serves as an oversight function within an organization’s governance framework.
ZH: 第二道防线在组织治理框架中承担监督职能

[v7u_N002570|2570] Although the second line operates independently from the front office, effective collaboration with the first line is essential to foster a culture of compliance.
ZH: 第二道防线独立于前台，但需有效协作以培育合规文化

[v7u_N002571|2571] Key aspects of this interaction include:
ZH: 第二道防线与前台互动的关键方面包括

[v7u_N002572|2572] Education and training: The second line approves training on regulatory requirements, risk management practices, and staff responsibilities, ensuring client-facing staff are equipped to identify risks and comply with AFC policies. External specialist providers or internal teams might develop the training.
ZH: 第二道防线审批监管要求与风险管理培训，确保前台人员具备识别风险的能力

[v7u_N002573|2573] Advisory role: The second line offers guidance on best practices, emerging risks, and compliance obligations, allowing front office staff to make informed decisions.
ZH: 第二道防线提供最佳实践、新兴风险与合规义务的咨询指导

[v7u_N002574|2574] Risk awareness: The second line emphasizes the front office’s role as risk owners through policies and procedures. This helps staff to become more vigilant and to understand their part in managing client relationship and transaction risks.
ZH: 第二道防线通过政策与程序强调前台作为风险所有者的角色

[v7u_N002575|2575] An established culture of compliance offers several benefits, including:
ZH: 成熟的合规文化带来的益处包括

[v7u_N002576|2576] Informed decision-making: When front office staff understand their risk ownership responsibilities and are well-supported to manage risk, they can make informed decisions that help protect the organization from the threat of financial crime.
ZH: 前台人员理解风险所有权后能做出明智决策，保护组织免受金融犯罪威胁

[v7u_N002577|2577] Ownership of risk: Supporting front office personnel to understand financial crime risks throughout the client journey ensures that they take ownership of and manage those risks effectively.
ZH: 支持前台人员理解客户旅程中的金融犯罪风险，确保其有效承担风险管理责任

[v7u_N002578|2578] Prevention of issues: Second line and front office collaboration helps prevent compliance violations and associated reputational and financia risks.
ZH: 第二道防线与前台协作有助于预防合规违规及声誉与财务风险

[v7u_N002579|2579] Organizations often use responsible, accountable, consulted, and informed (RACI) matrices to clarify roles and responsibilities in risk ownership. These matrices define the relationships between teams, including those between the first and second lines. The RACI framework assigns specific roles, outlines who is responsible for managing risks, and who should be consulted or informed in risk-related decision-making.
ZH: RACI矩阵用于明确风险所有权中的角色与职责，定义第一道与第二道防线的关系

[v7u_N002580|2580] The RACI matrix reinforces the front office’s role in identifying, assessing, and managing risks.
ZH: RACI矩阵强化前台在识别、评估和管理风险中的角色

[v7u_N002581|2581] While the second line provides advice, guidance, and oversight, final decisions regarding client onboarding or relationship termination usually lie with the front office risk owners or relevant committees.
ZH: 第二道防线提供建议和监督，但客户准入或关系终止的最终决策权通常属于前台风险负责人或相关委员会。

[v7u_N002582|2582] In practice, committees with quorums that include both first- and second-line leaders often make business decisions about regulatory obligations related to business activities.
ZH: 由第一道和第二道防线负责人组成的委员会通常共同做出涉及监管义务的业务决策。

[v7u_N002583|2583] The second line should ensure that front office staff are equipped with the necessary tools to make informed choices, thus reinforcing collaborative decision-making.
ZH: 第二道防线应确保前台人员具备做出知情决策的必要工具，以加强协作决策。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002572"
    ],
    "proposition": "第二道防线审批培训，确保前台人员具备识别风险的能力。",
    "source_quotes": [
      "Education and training: The second line approves training on regulatory requirements, risk management practices, and staff responsibilities, ensuring client-facing staff are equipped to identify risks and comply with AFC policies. External specialist providers or internal teams might develop the training."
    ],
    "relation_cues": [
      "approves",
      "ensuring"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "第二道防线审批培训",
      "outcomes_or_paths": [
        "前台人员具备识别风险和遵守反金融犯罪政策的能力"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002572",
        "quote": "Education and training: The second line approves training on regulatory requirements, risk management practices, and staff responsibilities, ensuring client-facing staff are equipped to identify risks and comply with AFC policies. External specialist providers or internal teams might develop the training."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002573"
    ],
    "proposition": "第二道防线提供咨询指导，使前台做出知情决策。",
    "source_quotes": [
      "Advisory role: The second line offers guidance on best practices, emerging risks, and compliance obligations, allowing front office staff to make informed decisions."
    ],
    "relation_cues": [
      "offers",
      "allowing"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "第二道防线提供咨询指导",
      "outcomes_or_paths": [
        "前台人员做出知情决策"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002573",
        "quote": "Advisory role: The second line offers guidance on best practices, emerging risks, and compliance obligations, allowing front office staff to make informed decisions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002574"
    ],
    "proposition": "第二道防线通过政策程序强调前台作为风险所有者的角色，帮助员工保持警惕并理解其职责。",
    "source_quotes": [
      "Risk awareness: The second line emphasizes the front office’s role as risk owners through policies and procedures. This helps staff to become more vigilant and to understand their part in managing client relationship and transaction risks."
    ],
    "relation_cues": [
      "emphasizes",
      "helps"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "通过政策和程序"
      ],
      "focal_handling_or_judgment": "强调前台作为风险所有者的角色",
      "outcomes_or_paths": [
        "员工更加警惕并理解其在管理客户关系和交易风险中的职责"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002574",
        "quote": "Risk awareness: The second line emphasizes the front office’s role as risk owners through policies and procedures. This helps staff to become more vigilant and to understand their part in managing client relationship and transaction risks."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002581"
    ],
    "proposition": "第二道防线提供建议和监督，但客户准入或关系终止的最终决策权通常属于前台风险负责人或相关委员会。",
    "source_quotes": [
      "While the second line provides advice, guidance, and oversight, final decisions regarding client onboarding or relationship termination usually lie with the front office risk owners or relevant committees."
    ],
    "relation_cues": [
      "provides",
      "lie with"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "第二道防线提供建议、指导和监督"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "最终决策权归属判断",
      "outcomes_or_paths": [
        "最终决策权属于前台风险负责人或相关委员会"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002581",
        "quote": "While the second line provides advice, guidance, and oversight, final decisions regarding client onboarding or relationship termination usually lie with the front office risk owners or relevant committees."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002582"
    ],
    "proposition": "由第一道和第二道防线负责人组成的委员会通常共同做出涉及监管义务的业务决策。",
    "source_quotes": [
      "In practice, committees with quorums that include both first- and second-line leaders often make business decisions about regulatory obligations related to business activities."
    ],
    "relation_cues": [
      "often make"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "涉及与业务活动相关的监管义务"
      ],
      "focal_handling_or_judgment": "委员会做出业务决策",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002582",
        "quote": "In practice, committees with quorums that include both first- and second-line leaders often make business decisions about regulatory obligations related to business activities."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N002583"
    ],
    "proposition": "第二道防线应确保前台人员具备做出知情决策的必要工具，以加强协作决策。",
    "source_quotes": [
      "The second line should ensure that front office staff are equipped with the necessary tools to make informed choices, thus reinforcing collaborative decision-making."
    ],
    "relation_cues": [
      "should ensure",
      "reinforcing"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "第二道防线确保前台人员具备必要工具",
      "outcomes_or_paths": [
        "加强协作决策"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002583",
        "quote": "The second line should ensure that front office staff are equipped with the necessary tools to make informed choices, thus reinforcing collaborative decision-making."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
