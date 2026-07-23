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

section_id: `CH34-S10`

section_title: `Three lines of defense > Third line of defense AFC function`

section_text_with_unit_anchors:

```text
[v7u_N002517|2517] The third LOD in a financial institution's risk management framework is the internal audit function.
ZH: 第三道防线是金融机构风险管理框架中的内部审计职能

[v7u_N002518|2518] This line operates independently of the first two lines.
ZH: 第三道防线独立于前两道防线运作

[v7u_N002519|2519] The first line handles risk ownership and operational management, while the second line focuses on advisory, policy, and compliance monitoring.
ZH: 第一道防线负责风险所有权和运营管理，第二道防线专注于咨询、政策和合规监控

[v7u_N002520|2520] The third line’s primary purpose is to objectively assess the effectiveness of the organization’s AFC risk management, governance, and control processes.
ZH: 第三道防线的主要目的是客观评估组织金融犯罪防控风险管理、治理和控制流程的有效性

[v7u_N002521|2521] The independent audit function is the fourth pillar of an AML program.
ZH: 独立审计职能是反洗钱项目的第四道防线。

[v7u_N002522|2522] This function verifies and validates the organization’s compliance efforts.
ZH: 独立审计职能负责验证和确认组织的合规工作。

[v7u_N002523|2523] In a robust AML program, the independent audit function reports directly to the audit committee or board of directors. This ensures that the findings are independent and not influenced by any other priorities.
ZH: 独立审计职能直接向审计委员会或董事会报告以确保独立性。

[v7u_N002524|2524] The independent audit function acts as a cross-check on the effectiveness of the first and second lines of defense. Independent auditors assess operational and compliance frameworks to ensure the organization’s controls align with regulatory requirements and function effectively.
ZH: 独立审计职能对第一道和第二道防线的有效性进行交叉检查。

[v7u_N002525|2525] Each LOD has different responsibilities and performs specific checks. The first line focuses on daily execution accuracy, with responsibilities including frontline operational management. The checks and controls in this line include:
ZH: 第一道防线负责日常执行准确性，包括一线运营管理。

[v7u_N002526|2526] QC checks to ensure procedures and guidelines are followed.
ZH: 质量控制检查确保遵循程序和指南。

[v7u_N002527|2527] QA checks to evaluate the effectiveness of processes and systems operated by the first line.
ZH: 质量保证检查评估第一道防线流程和系统的有效性。

[v7u_N002528|2528] Control testing to assess the design and operational effectiveness of controls.
ZH: 控制测试评估控制的设计和运行有效性。

[v7u_N002529|2529] The second LOD focuses on framework effectiveness. This line includes compliance functions, ensuring adherence to laws, regulations, and internal policies. The checks in this line include:
ZH: 第二道防线关注框架有效性，包括合规职能。

[v7u_N002530|2530] Compliance monitoring: Ongoing oversight to ensure adherence to policies and regulations.
ZH: 合规监控：持续监督以确保遵守政策和法规。

[v7u_N002531|2531] Testing procedures: Regular compliance tests to verify whether the first line has implemented policies effectively and if controls operate as intended.
ZH: 定期合规测试以验证第一道防线政策实施和控制的运行情况。

[v7u_N002532|2532] QA checks: Evaluate the effectiveness of processes and systems operated by the second line.
ZH: 质量保证检查评估第二道防线流程和系统的有效性。

[v7u_N002533|2533] The third line focuses on systematic issues and governance. The independent audit function carries out its role through:
ZH: 第三道防线关注系统性问题与治理，独立审计职能通过以下方式履行职责。

[v7u_N002534|2534] Independent audits: Assess the effectiveness and efficiency of the firstand second-line controls. Auditors ensure that the AML program meets regulatory requirements and industry standards, identifying and communicating deficiencies.
ZH: 独立审计评估第一、二道防线控制的有效性和效率，确保反洗钱项目符合监管要求。

[v7u_N002535|2535] These distinct checks at each LOD are critical for maintaining an effective risk management system. Collectively, they ensure:
ZH: 各道防线的不同检查对于维持有效的风险管理体系至关重要。

[v7u_N002536|2536] The first line’s operational systems execute policies and follow procedures.
ZH: 第一道防线的运营系统执行政策并遵循程序。

[v7u_N002537|2537] The second line’s compliance functions follow policies, participate in investigations, verify procedure effectiveness, and provide oversight.
ZH: 第二道防线的合规职能遵循政策、参与调查、验证程序有效性并提供监督。

[v7u_N002538|2538] The third line’s independent audit reviews risks and controls, offering an unbiased opinion on the control environment’s effectiveness.
ZH: 第三道防线的独立审计审查风险和控制，提供关于控制环境有效性的客观意见。

[v7u_N002539|2539] In smaller organizations that lack the resources for an internal audit team, or when there are skill or resource limitations, external auditors might perform the independent audit function.
ZH: 在缺乏内部审计资源的小型组织中，可由外部审计师执行独立审计职能。

[v7u_N002540|2540] When well executed, this external perspective enriches the audit process and provides an unbiased assessment of the AFC compliance program and risk management effectiveness.
ZH: 外部视角可丰富审计过程，提供对金融犯罪防控合规项目及风险管理有效性的客观评估。

[v7u_N002541|2541] By maintaining these checks and balances at each LOD, organizations can identify weaknesses and enhance their AFC compliance programs, mitigating financial crime risks.
ZH: 三道防线中的制衡机制有助于识别弱点并加强金融犯罪防控合规计划。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002523"
    ],
    "proposition": "独立审计职能直接向审计委员会或董事会报告以确保独立性。",
    "source_quotes": [
      "In a robust AML program, the independent audit function reports directly to the audit committee or board of directors. This ensures that the findings are independent and not influenced by any other priorities."
    ],
    "relation_cues": [
      "reports directly to",
      "ensures"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "独立审计职能运作"
      ],
      "basis_or_condition": [
        "需要确保独立性"
      ],
      "focal_handling_or_judgment": "独立审计职能直接向审计委员会或董事会报告",
      "outcomes_or_paths": [
        "发现独立且不受其他优先事项影响"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002523",
        "quote": "In a robust AML program, the independent audit function reports directly to the audit committee or board of directors. This ensures that the findings are independent and not influenced by any other priorities."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002524",
      "v7u_N002534",
      "v7u_N002538"
    ],
    "proposition": "独立审计职能对第一、二道防线进行交叉检查，评估其控制的有效性和效率，确保AML符合要求，并识别传达缺陷，提供关于控制环境有效性的无偏见意见。",
    "source_quotes": [
      "The independent audit function acts as a cross-check on the effectiveness of the first and second lines of defense. Independent auditors assess operational and compliance frameworks to ensure the organization’s controls align with regulatory requirements and function effectively.",
      "Independent audits: Assess the effectiveness and efficiency of the firstand second-line controls. Auditors ensure that the AML program meets regulatory requirements and industry standards, identifying and communicating deficiencies.",
      "The third line’s independent audit reviews risks and controls, offering an unbiased opinion on the control environment’s effectiveness."
    ],
    "relation_cues": [
      "acts as a cross-check",
      "assess",
      "ensure",
      "identifying",
      "offering"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织需要确保控制符合法规并有效运作"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "独立审计评估第一、二道防线控制的有效性和效率，确保AML合规",
      "outcomes_or_paths": [
        "识别并沟通缺陷",
        "提供关于控制环境有效性的无偏见意见"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002524",
        "quote": "The independent audit function acts as a cross-check on the effectiveness of the first and second lines of defense. Independent auditors assess operational and compliance frameworks to ensure the organization’s controls align with regulatory requirements and function effectively."
      },
      {
        "unit_id": "v7u_N002534",
        "quote": "Independent audits: Assess the effectiveness and efficiency of the firstand second-line controls. Auditors ensure that the AML program meets regulatory requirements and industry standards, identifying and communicating deficiencies."
      },
      {
        "unit_id": "v7u_N002538",
        "quote": "The third line’s independent audit reviews risks and controls, offering an unbiased opinion on the control environment’s effectiveness."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002539",
      "v7u_N002540"
    ],
    "proposition": "当缺乏内部审计资源或技能时，外部审计师可能执行独立审计职能，提供对AFC合规和风险管理有效性的客观评估。",
    "source_quotes": [
      "In smaller organizations that lack the resources for an internal audit team, or when there are skill or resource limitations, external auditors might perform the independent audit function.",
      "When well executed, this external perspective enriches the audit process and provides an unbiased assessment of the AFC compliance program and risk management effectiveness."
    ],
    "relation_cues": [
      "lack",
      "might perform",
      "provides"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织缺乏内部审计资源或技能"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "外部审计师执行独立审计职能",
      "outcomes_or_paths": [
        "提供对AFC合规和风险管理有效性的客观评估"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002539",
        "quote": "In smaller organizations that lack the resources for an internal audit team, or when there are skill or resource limitations, external auditors might perform the independent audit function."
      },
      {
        "unit_id": "v7u_N002540",
        "quote": "When well executed, this external perspective enriches the audit process and provides an unbiased assessment of the AFC compliance program and risk management effectiveness."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
