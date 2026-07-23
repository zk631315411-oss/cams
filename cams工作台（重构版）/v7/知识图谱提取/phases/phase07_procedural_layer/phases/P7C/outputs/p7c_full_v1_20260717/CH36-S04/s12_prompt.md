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

section_id: `CH36-S04`

section_title: `Types of risk assessment > The risk appetite statement`

section_text_with_unit_anchors:

```text
[v7u_N002690|2690] Risk appetite is the level of financial crime risk acceptable to an organization, within the parameters of its business and strategic goals.
ZH: 风险偏好是机构在业务和战略目标内可接受的风险水平

[v7u_N002691|2691] The organization’s risk appetite statement (RAS) must be approved by the board of directors and periodically reviewed to consider any changes in the business and relevant risk factors.
ZH: 风险偏好声明需经董事会批准并定期审查

[v7u_N002692|2692] The organization’s risk appetite might change over time.
ZH: 机构的风险偏好可能随时间变化

[v7u_N002693|2693] For example, an organization seeks a merger with another entity that has been traditionally involved in higher risk activities. This situation implies the newly formed organization’s risk appetite has changed and will now include higher risk activities.
ZH: 合并可能导致风险偏好变化，纳入高风险活动

[v7u_N002694|2694] The board of directors sets the risk appetite statement and tolerance levels.
ZH: 董事会设定风险偏好声明和容忍度

[v7u_N002695|2695] Business executives are accountable for managing risk limits within their business units.
ZH: 业务高管负责管理其业务单元内的风险限额

[v7u_N002696|2696] To implement a risk appetite framework, you must determine the types of risk the organization is willing to accept to meet its strategic objectives, set its risk tolerance level, and create a risk appetite statement.
ZH: 实施风险偏好框架需确定风险类型、容忍度并制定声明

[v7u_N002697|2697] The risk appetite statement should be easy for all stakeholders to understand. The information in the statement should be positive.
ZH: 风险偏好声明应易于理解且内容积极

[v7u_N002698|2698] It should include key background information and assumptions, strategic and financial plans, and quantitative measures that translate into risk limits.
ZH: 风险偏好声明应包含背景信息、战略财务计划和量化指标

[v7u_N002699|2699] Over time, the organization might periodically reassess its risk exposure and adjust its risk appetite statement.
ZH: 机构可能定期重新评估风险敞口并调整风险偏好声明

[v7u_N002700|2700] For example, a potential new customer might raise an organization’s risk exposure. The organization can choose to reject the customer, limit access to certain products or services, or place enhanced risk controls on the customer’s account.
ZH: 新客户可能提高风险敞口，机构可选择拒绝或加强控制

[v7u_N002701|2701] The organization might use the same risk appetite statement to review customers who no longer meet the organization’s risk appetite.
ZH: 使用风险偏好声明审查不再符合风险偏好的现有客户

[v7u_N002702|2702] Risk limits allocate the organization’s overall risk appetite to appropriate business units with specific risk categories and concentrations for each.
ZH: 风险限额将整体风险偏好分配到具体业务单元并设定风险类别和集中度

[v7u_N002703|2703] Lastly, the organization needs to conduct regular independent assessments to make sure internal risk controls, risk management, and risk governance are effective and functioning properly.
ZH: 机构必须定期进行独立评估以确保风险控制、管理和治理有效
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002691"
    ],
    "proposition": "风险偏好声明必须经董事会批准并定期审查，以考虑业务和风险因素的变化。",
    "source_quotes": [
      "The organization’s risk appetite statement (RAS) must be approved by the board of directors and periodically reviewed to consider any changes in the business and relevant risk factors."
    ],
    "relation_cues": [
      "must",
      "periodically",
      "to consider"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "考虑业务和相关风险因素的变化"
      ],
      "focal_handling_or_judgment": "风险偏好声明须经董事会批准并定期审查",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002691",
        "quote": "The organization’s risk appetite statement (RAS) must be approved by the board of directors and periodically reviewed to consider any changes in the business and relevant risk factors."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002693"
    ],
    "proposition": "组织合并可能导致风险偏好变化，纳入更高风险活动。",
    "source_quotes": [
      "For example, an organization seeks a merger with another entity that has been traditionally involved in higher risk activities. This situation implies the newly formed organization’s risk appetite has changed and will now include higher risk activities."
    ],
    "relation_cues": [
      "merger",
      "implies",
      "changed"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织寻求与从事高风险活动的实体合并"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "风险偏好改变，纳入更高风险活动",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002693",
        "quote": "For example, an organization seeks a merger with another entity that has been traditionally involved in higher risk activities. This situation implies the newly formed organization’s risk appetite has changed and will now include higher risk activities."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002696"
    ],
    "proposition": "实施风险偏好框架必须确定风险类型、设定容忍度并制定风险偏好声明。",
    "source_quotes": [
      "To implement a risk appetite framework, you must determine the types of risk the organization is willing to accept to meet its strategic objectives, set its risk tolerance level, and create a risk appetite statement."
    ],
    "relation_cues": [
      "must",
      "determine",
      "set",
      "create"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "实施风险偏好框架"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "确定风险类型、设定风险容忍度、制定风险偏好声明",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002696",
        "quote": "To implement a risk appetite framework, you must determine the types of risk the organization is willing to accept to meet its strategic objectives, set its risk tolerance level, and create a risk appetite statement."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002699"
    ],
    "proposition": "机构可能定期重新评估风险敞口并调整风险偏好声明。",
    "source_quotes": [
      "Over time, the organization might periodically reassess its risk exposure and adjust its risk appetite statement."
    ],
    "relation_cues": [
      "Over time",
      "might",
      "periodically"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "随时间推移"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "定期重新评估风险敞口并调整风险偏好声明",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002699",
        "quote": "Over time, the organization might periodically reassess its risk exposure and adjust its risk appetite statement."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002700"
    ],
    "proposition": "当潜在新客户可能提高风险敞口时，机构可选择拒绝客户、限制产品服务或加强风险控制。",
    "source_quotes": [
      "For example, a potential new customer might raise an organization’s risk exposure. The organization can choose to reject the customer, limit access to certain products or services, or place enhanced risk controls on the customer’s account."
    ],
    "relation_cues": [
      "might raise",
      "choose",
      "reject",
      "limit",
      "place"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "潜在新客户可能提高组织风险敞口"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "机构做出应对决策",
      "outcomes_or_paths": [
        "拒绝客户",
        "限制特定产品或服务",
        "加强风险控制"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002700",
        "quote": "For example, a potential new customer might raise an organization’s risk exposure. The organization can choose to reject the customer, limit access to certain products or services, or place enhanced risk controls on the customer’s account."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N002701"
    ],
    "proposition": "组织可使用同一风险偏好声明审查不再符合其风险偏好的现有客户。",
    "source_quotes": [
      "The organization might use the same risk appetite statement to review customers who no longer meet the organization’s risk appetite."
    ],
    "relation_cues": [
      "might",
      "use",
      "review",
      "no longer meet"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "现有客户不再符合组织风险偏好"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "使用风险偏好声明审查客户",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002701",
        "quote": "The organization might use the same risk appetite statement to review customers who no longer meet the organization’s risk appetite."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N002703"
    ],
    "proposition": "组织必须定期进行独立评估，确保内部风险控制、管理和治理有效运作。",
    "source_quotes": [
      "Lastly, the organization needs to conduct regular independent assessments to make sure internal risk controls, risk management, and risk governance are effective and functioning properly."
    ],
    "relation_cues": [
      "needs to",
      "regular",
      "independent",
      "make sure"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "定期"
      ],
      "basis_or_condition": [
        "确保风险控制、管理和治理有效"
      ],
      "focal_handling_or_judgment": "进行独立评估",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002703",
        "quote": "Lastly, the organization needs to conduct regular independent assessments to make sure internal risk controls, risk management, and risk governance are effective and functioning properly."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
