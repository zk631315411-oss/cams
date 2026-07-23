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

section_id: `CH37-S03`

section_title: `Enterprise-wide risk assessment > Measuring control effectiveness`

section_text_with_unit_anchors:

```text
[v7u_N002769|2769] The formula for calculating residual risk is: inherent risk minus control effectiveness equals residual risk (inherent risk – control effectiveness = residual risk).
ZH: 剩余风险计算公式：固有风险减去控制有效性

[v7u_N002770|2770] AML/CFT measures, policies, procedures, systems, and controls might be already in place or still under development.
ZH: 反洗钱/反恐怖融资措施可能已到位或仍在开发中

[v7u_N002771|2771] Organizations should evaluate these control measures to determine their effectiveness in reducing inherent risks.
ZH: 组织应评估控制措施在降低固有风险方面的有效性

[v7u_N002772|2772] The effectiveness depends on proper application, functionality, and consistency throughout the organization.
ZH: 控制有效性取决于正确应用、功能性和全组织的一致性

[v7u_N002773|2773] In conducting a risk assessment, once an organization identifies inherent risks, it must apply control measures to mitigate them to an acceptable level of residual risk.
ZH: 识别固有风险后，必须应用控制措施将其降至可接受的剩余风险水平

[v7u_N002774|2774] Control measures are designed to reduce the inherent AML/CTF risk with customers, jurisdictions, products, and delivery channels to a level consistent with the organization’s risk appetite statement.
ZH: 控制措施旨在将客户、地域、产品和渠道的固有反洗钱/反恐怖融资风险降至与风险偏好一致的水平

[v7u_N002775|2775] For example, if the inherent risk of onboarding PEPs is high, the organization might implement EDD, request source of funds and source of wealth verification, and increase business relationship monitoring. If these controls are judged to be effective, the result may be lowered to medium or low residual risk.
ZH: 示例：对政治敏感人物的固有风险高时，实施EDD、核实资金来源和财富、加强监控，有效则剩余风险降低

[v7u_N002776|2776] Control measures should be assessed for both design and operational effectiveness.
ZH: 控制措施应从设计和运行有效性两方面进行评估

[v7u_N002777|2777] Design effectiveness evaluates whether the control is appropriately built for mitigating inherent risk.
ZH: 设计有效性评估控制是否适当构建以缓解固有风险

[v7u_N002778|2778] For example, if the control is intended to perform EDD for PEPs, design effectiveness ensures the process outlines all salient requirements identified in the policy in performing EDD and reporting results.
ZH: 示例：针对政治敏感人物的EDD控制，设计有效性确保流程涵盖政策要求并报告结果

[v7u_N002779|2779] If there are gaps or flaws in the process design, the control must be redesigned.
ZH: 如果流程设计存在缺陷，必须重新设计控制

[v7u_N002780|2780] Design effectiveness can be tested before and after a control is live.
ZH: 设计有效性可在控制上线前后进行测试

[v7u_N002781|2781] Operational effectiveness determines if the control is functioning as intended.
ZH: 运营有效性定义：控制是否按预期运行

[v7u_N002782|2782] For example, if two out of ten KYC files examined lack sanction screening results, this indicates an operational failure caused by human or system error.
ZH: 了解你的客户文件缺少制裁筛查结果属于运营失效示例

[v7u_N002783|2783] The organization must analyze and correct the root cause of the error to avoid recurrence.
ZH: 组织必须分析并纠正错误的根本原因以避免再次发生

[v7u_N002784|2784] In this instance, the organization might need to redesign the QC process, as the missing screening results were not captured. Additional training might be needed if human error is identified.
ZH: 运营失效的补救措施：重新设计QC流程或增加培训

[v7u_N002785|2785] To measure operational effectiveness successfully, the control needs to operate for a sufficient period of time.
ZH: 衡量运营有效性需要控制运行足够长的时间

[v7u_N002786|2786] For example, if a control operates monthly, a minimum of three to six months of data would be needed to establish whether the control is operating effectively.
ZH: 月度控制至少需要3-6个月数据来判断有效性
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002773"
    ],
    "proposition": "识别固有风险后，必须应用控制措施将其降至可接受的剩余风险水平。",
    "source_quotes": [
      "In conducting a risk assessment, once an organization identifies inherent risks, it must apply control measures to mitigate them to an acceptable level of residual risk."
    ],
    "relation_cues": [
      "once",
      "must"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织识别出固有风险"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "应用控制措施",
      "outcomes_or_paths": [
        "将固有风险降至可接受的剩余风险水平"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002773",
        "quote": "In conducting a risk assessment, once an organization identifies inherent risks, it must apply control measures to mitigate them to an acceptable level of residual risk."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002775"
    ],
    "proposition": "对高固有风险的PEPs，实施EDD、核实资金来源和财富、加强监控；如果控制有效，则剩余风险降至中低。",
    "source_quotes": [
      "if the inherent risk of onboarding PEPs is high, the organization might implement EDD, request source of funds and source of wealth verification, and increase business relationship monitoring. If these controls are judged to be effective, the result may be lowered to medium or low residual risk."
    ],
    "relation_cues": [
      "if",
      "might",
      "if",
      "judged effective",
      "may"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "政治敏感人物（PEPs）的固有风险高"
      ],
      "basis_or_condition": [
        "控制措施被判断为有效"
      ],
      "focal_handling_or_judgment": "实施强化尽职调查（EDD）、核实资金来源和财富、加强监控",
      "outcomes_or_paths": [
        "控制有效时剩余风险降至中低"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002775",
        "quote": "if the inherent risk of onboarding PEPs is high, the organization might implement EDD, request source of funds and source of wealth verification, and increase business relationship monitoring. If these controls are judged to be effective, the result may be lowered to medium or low residual risk."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002779"
    ],
    "proposition": "如果控制流程设计存在缺陷，则必须重新设计控制。",
    "source_quotes": [
      "If there are gaps or flaws in the process design, the control must be redesigned."
    ],
    "relation_cues": [
      "if",
      "must"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "控制流程设计存在缺陷或漏洞"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "重新设计控制",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002779",
        "quote": "If there are gaps or flaws in the process design, the control must be redesigned."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002783",
      "v7u_N002784"
    ],
    "proposition": "当运营失效时，组织必须分析并纠正根本原因，并可能需要重新设计QC流程或提供额外培训。",
    "source_quotes": [
      "The organization must analyze and correct the root cause of the error to avoid recurrence.",
      "the organization might need to redesign the QC process, as the missing screening results were not captured. Additional training might be needed if human error is identified."
    ],
    "relation_cues": [
      "must",
      "might",
      "if"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "运营失效（如KYC文件缺少制裁筛查结果）"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "分析并纠正错误的根本原因",
      "outcomes_or_paths": [
        "可能重新设计QC流程",
        "如果识别出人为错误，可能需要额外培训"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002783",
        "quote": "The organization must analyze and correct the root cause of the error to avoid recurrence."
      },
      {
        "unit_id": "v7u_N002784",
        "quote": "the organization might need to redesign the QC process, as the missing screening results were not captured. Additional training might be needed if human error is identified."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
