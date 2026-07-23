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

section_id: `CH06-S09`

section_title: `Money Laundering Risks in Financial Services > Politically exposed person risks`

section_text_with_unit_anchors:

```text
[v7u_N000457|457] A politically exposed person (PEP) is an individual in a prominent political function, their immediate family, close associates, and any businesses held or controlled by that person.
ZH: 政治敏感人物（政治敏感人物）的定义：担任重要公职的个人及其亲属和密切关联人

[v7u_N000458|458] One challenge in identifying PEPs is the varying guidance and recommendations in each jurisdiction.
ZH: 识别政治敏感人物的挑战在于各司法管辖区指引不同

[v7u_N000459|459] Organizations must adhere to their local regulatory requirements in identifying PEPs.
ZH: 机构必须遵守当地监管要求识别政治敏感人物

[v7u_N000460|460] However, organizations may choose to enforce higher standards based on their risk appetite.
ZH: 机构可根据风险偏好执行更高的政治敏感人物标准

[v7u_N000461|461] According to the Financial Action Task Force (FATF), there are three types of PEPs:
ZH: FATF将政治敏感人物分为三类

[v7u_N000462|462] Foreign PEPs are individuals entrusted with prominent public functions by a foreign country.
ZH: 外国政治敏感人物指受外国委托担任重要公共职能的个人

[v7u_N000463|463] Domestic PEPs are individuals entrusted domestically with prominent public functions.
ZH: 国内政治敏感人物指在国内担任重要公共职能的个人

[v7u_N000464|464] International organization PEPs are individuals from an international organization entrusted with a prominent function such as secretary general, executive director, or president.
ZH: 国际组织政治敏感人物指在国际组织中担任秘书长、执行董事或主席等要职的个人

[v7u_N000465|465] Individuals in high positions and their associates are more vulnerable to corruption.
ZH: 高层职位个人及其关联人更易受腐败影响

[v7u_N000466|466] Corruption might be favors where the PEP directs government contracts to an organization in return for kickbacks. In addition, a PEP might influence legislation for bribes or flee the country with government funds.
ZH: 政治敏感人物腐败示例：以政府合同换取回扣、影响立法收受贿赂或携政府资金潜逃

[v7u_N000467|467] Use a broad definition for defining a PEP.
ZH: 应采用宽泛定义来界定政治敏感人物

[v7u_N000468|468] PEPs can generally be defined as:
ZH: 政治敏感人物的一般定义

[v7u_N000469|469] A person in a prominent decision-making or influential role
ZH: 政治敏感人物指担任重要决策或有影响力角色的人

[v7u_N000470|470] A person within royal, military, legislative, judicial, executive, or similar government positions
ZH: 政治敏感人物包括王室、军事、立法、司法、行政或类似政府职位的人

[v7u_N000471|471] PEPs will often use nominees or businesses they are associated with.
ZH: 政治敏感人物常使用名义人或关联企业

[v7u_N000472|472] Therefore, the definition of PEP can also include:
ZH: 政治敏感人物定义还可包括以下人员

[v7u_N000473|473] Immediate family
ZH: 政治敏感人物的直系亲属

[v7u_N000474|474] Close friends or associates
ZH: 政治敏感人物的密友或关联人

[v7u_N000475|475] Businesses owned or held by those individuals
ZH: 政治敏感人物拥有或持有的企业

[v7u_N000476|476] Under a risk-based approach, PEP risk is manageable.
ZH: 基于风险的方法下，政治敏感人物风险是可控的

[v7u_N000477|477] Some organizations follow a “once a PEP, always a PEP” approach because the individual may remain in the same circles of influence, even if they have stepped down.
ZH: 部分机构采用“一旦是政治敏感人物，永远是政治敏感人物”的方法

[v7u_N000478|478] Other organizations will look at:
ZH: 其他机构会考察以下因素

[v7u_N000479|479] The individual’s influence at the time, such as their ability to award contracts or allocate funds
ZH: 考察个人当时的影响力，如授予合同或分配资金的能力

[v7u_N000480|480] How long the individual has been classified as a PEP
ZH: 考察个人被归类为政治敏感人物的时间长短

[v7u_N000481|481] The purpose of the PEP designation is important.
ZH: 政治敏感人物 认定的目的具有重要意义

[v7u_N000482|482] Organizations must take the necessary steps to adapt transaction monitoring and KYC reviews and escalate based on their risk appetite.
ZH: 机构必须根据风险偏好调整交易监控和 了解你的客户 审查
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000459"
    ],
    "proposition": "机构必须遵守当地监管要求识别政治敏感人物。",
    "source_quotes": [
      "Organizations must adhere to their local regulatory requirements in identifying PEPs."
    ],
    "relation_cues": [
      "must",
      "in identifying"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "识别政治敏感人物"
      ],
      "basis_or_condition": [
        "当地监管要求"
      ],
      "focal_handling_or_judgment": "遵守当地监管要求",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000459",
        "quote": "Organizations must adhere to their local regulatory requirements in identifying PEPs."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N000460"
    ],
    "proposition": "机构可根据风险偏好执行更高的政治敏感人物标准。",
    "source_quotes": [
      "However, organizations may choose to enforce higher standards based on their risk appetite."
    ],
    "relation_cues": [
      "may",
      "based on"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "机构的风险偏好"
      ],
      "basis_or_condition": [
        "基于风险偏好"
      ],
      "focal_handling_or_judgment": "执行更高的政治敏感人物标准",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000460",
        "quote": "However, organizations may choose to enforce higher standards based on their risk appetite."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N000467"
    ],
    "proposition": "应采用宽泛定义来界定政治敏感人物。",
    "source_quotes": [
      "Use a broad definition for defining a PEP."
    ],
    "relation_cues": [
      "use"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "界定政治敏感人物"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "使用宽泛定义",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000467",
        "quote": "Use a broad definition for defining a PEP."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N000477"
    ],
    "proposition": "部分机构采用“一旦是政治敏感人物，永远是政治敏感人物”的方法。",
    "source_quotes": [
      "Some organizations follow a “once a PEP, always a PEP” approach because the individual may remain in the same circles of influence, even if they have stepped down."
    ],
    "relation_cues": [
      "once a PEP, always a PEP",
      "because"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "个人曾是政治敏感人物"
      ],
      "basis_or_condition": [
        "个人可能仍留在相同影响圈"
      ],
      "focal_handling_or_judgment": "持续将该个人视为政治敏感人物",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000477",
        "quote": "Some organizations follow a “once a PEP, always a PEP” approach because the individual may remain in the same circles of influence, even if they have stepped down."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N000478",
      "v7u_N000479",
      "v7u_N000480"
    ],
    "proposition": "其他机构会考察个人当时的影响力和被归类为政治敏感人物的时长等因素来决定是否继续视为政治敏感人物。",
    "source_quotes": [
      "Other organizations will look at:",
      "The individual’s influence at the time, such as their ability to award contracts or allocate funds",
      "How long the individual has been classified as a PEP"
    ],
    "relation_cues": [
      "look at",
      "influence",
      "classified"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "需要判断是否继续将个人视为政治敏感人物"
      ],
      "basis_or_condition": [
        "个人当时的影响力",
        "个人被归类为政治敏感人物的时长"
      ],
      "focal_handling_or_judgment": "考察这些因素并作出判断",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000478",
        "quote": "Other organizations will look at:"
      },
      {
        "unit_id": "v7u_N000479",
        "quote": "The individual’s influence at the time, such as their ability to award contracts or allocate funds"
      },
      {
        "unit_id": "v7u_N000480",
        "quote": "How long the individual has been classified as a PEP"
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N000482"
    ],
    "proposition": "机构必须根据风险偏好采取必要步骤调整交易监控和KYC审查并升级。",
    "source_quotes": [
      "Organizations must take the necessary steps to adapt transaction monitoring and KYC reviews and escalate based on their risk appetite."
    ],
    "relation_cues": [
      "must",
      "based on"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "面对政治敏感人物风险"
      ],
      "basis_or_condition": [
        "基于风险偏好"
      ],
      "focal_handling_or_judgment": "调整交易监控和KYC审查并升级",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000482",
        "quote": "Organizations must take the necessary steps to adapt transaction monitoring and KYC reviews and escalate based on their risk appetite."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
