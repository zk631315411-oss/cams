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

section_id: `CH19-S04`

section_title: `Financial Action Task Force > FATF Recommendations 24-40`

section_text_with_unit_anchors:

```text
[v7u_N001367|1367] FATF Recommendations 24 to 40 outline key measures to strengthen transparency, institutional oversight, and global cooperation in AML/CFT efforts.
ZH: FATF建议24-40概述加强透明度、机构监督和全球合作的关键措施

[v7u_N001368|1368] Recommendations 24 and 25 advise jurisdictions to assess the risk of misuse of legal persons and legal arrangements.
ZH: FATF建议24和25要求各辖区评估法人和法律安排被滥用的风险

[v7u_N001369|1369] Jurisdictions should also ensure competent authorities can access accurate, up-to-date beneficial ownership information on legal persons and trusts, requiring trustees to obtain and maintain such data for transparency and compliance.
ZH: 各辖区应确保主管机关能获取准确、最新的受益所有人信息

[v7u_N001370|1370] Jurisdictions should not permit legal persons to issue new bearer shares or bearer share warrants and should take measures to prevent the misuse of these types of stocks and documents.
ZH: 各辖区不应允许法人发行新的不记名股票或不记名认股权证

[v7u_N001371|1371] Recommendations 26 to 35 advise jurisdictions to ensure financial institutions are properly regulated and supervised to implement FATF Recommendations effectively.
ZH: FATF建议26-35要求各辖区确保金融机构受到适当监管以有效实施FATF建议

[v7u_N001372|1372] Supervisors should have sufficient authority, resources, and independence to monitor compliance, conduct inspections, and impose sanctions.
ZH: 监管机构应具备充分的权力、资源和独立性以监督合规并实施制裁

[v7u_N001373|1373] Jurisdictions should subject DNFBPs to licensing, registration, and supervision by competent authorities or self-regulatory bodies.
ZH: 各辖区应对指定非金融行业和职业实施许可、注册和监管

[v7u_N001374|1374] Jurisdictions should establish an FIU to analyze suspicious transaction reports and support law enforcement investigations.
ZH: 各辖区应设立金融情报机构以分析可疑交易报告并支持执法调查

[v7u_N001375|1375] Authorities should have powers to track, freeze, and seize criminal assets, enforce cross-border currency controls, and collect AML/CFT statistics.
ZH: 主管机关应有权追踪、冻结和扣押犯罪资产并实施跨境货币管制

[v7u_N001376|1376] Jurisdictions should have clear guidelines, feedback, and proportionate sanctions in place to ensure compliance and enforcement.
ZH: 各辖区应制定明确的指引、反馈和相称的制裁以确保合规与执行

[v7u_N001377|1377] Recommendations 36 to 40 advise jurisdictions to swiftly adopt and fully implement the Vienna, Palermo, and Terrorist Financing Conventions, along with other relevant international agreements.
ZH: 各辖区应迅速采纳并全面实施维也纳公约、巴勒莫公约和反恐融资公约

[v7u_N001378|1378] Jurisdictions should provide broad mutual legal assistance for money laundering and terrorist financing cases, ensuring efficient processes for handling such requests.
ZH: 各辖区应为洗钱和恐怖融资案件提供广泛的司法协助

[v7u_N001379|1379] Jurisdictions should take rapid action to identify, freeze, seize, and confiscate criminal assets at the request of foreign authorities.
ZH: 各辖区应应外国当局请求迅速采取行动识别、冻结、扣押和没收犯罪资产

[v7u_N001380|1380] Additionally, they should ensure extradition for money laundering and terrorist financing, including prosecuting nationals if extradition is not possible.
ZH: 各辖区应确保对洗钱和恐怖融资进行引渡，包括在无法引渡时起诉本国国民

[v7u_N001381|1381] Authorities should facilitate international cooperation through information exchange and joint investigations to combat financial crimes effectively on a global scale.
ZH: FATF建议要求当局通过信息交换和联合调查促进国际合作以打击金融犯罪。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001368"
    ],
    "proposition": "FATF建议24和25要求各辖区评估法人和法律安排被滥用的风险。",
    "source_quotes": [
      "Recommendations 24 and 25 advise jurisdictions to assess the risk of misuse of legal persons and legal arrangements."
    ],
    "relation_cues": [
      "advise",
      "assess"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "法人和法律安排被滥用的风险"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "评估滥用风险",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001368",
        "quote": "Recommendations 24 and 25 advise jurisdictions to assess the risk of misuse of legal persons and legal arrangements."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001369"
    ],
    "proposition": "各辖区应确保主管机关能获取准确、最新的受益所有人信息，并要求受托人获取和维护此类数据。",
    "source_quotes": [
      "Jurisdictions should also ensure competent authorities can access accurate, up-to-date beneficial ownership information on legal persons and trusts, requiring trustees to obtain and maintain such data for transparency and compliance."
    ],
    "relation_cues": [
      "should",
      "ensure",
      "requiring"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "需要获取受益所有人信息"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "确保主管机关可获取准确、最新的受益所有人信息",
      "outcomes_or_paths": [
        "透明和合规"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001369",
        "quote": "Jurisdictions should also ensure competent authorities can access accurate, up-to-date beneficial ownership information on legal persons and trusts, requiring trustees to obtain and maintain such data for transparency and compliance."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001370"
    ],
    "proposition": "各辖区不应允许法人发行新的不记名股票或不记名认股权证，并应采取措施防止滥用此类股票和文件。",
    "source_quotes": [
      "Jurisdictions should not permit legal persons to issue new bearer shares or bearer share warrants and should take measures to prevent the misuse of these types of stocks and documents."
    ],
    "relation_cues": [
      "should not",
      "permit",
      "take measures"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "法人发行不记名股票或认股权证"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "禁止发行并采取措施防止滥用",
      "outcomes_or_paths": [
        "防止滥用"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001370",
        "quote": "Jurisdictions should not permit legal persons to issue new bearer shares or bearer share warrants and should take measures to prevent the misuse of these types of stocks and documents."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N001371"
    ],
    "proposition": "FATF建议26-35要求各辖区确保金融机构受到适当监管以有效实施FATF建议。",
    "source_quotes": [
      "Recommendations 26 to 35 advise jurisdictions to ensure financial institutions are properly regulated and supervised to implement FATF Recommendations effectively."
    ],
    "relation_cues": [
      "advise",
      "ensure"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "金融机构监管"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "确保金融机构受到适当监管",
      "outcomes_or_paths": [
        "有效实施FATF建议"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001371",
        "quote": "Recommendations 26 to 35 advise jurisdictions to ensure financial institutions are properly regulated and supervised to implement FATF Recommendations effectively."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N001372"
    ],
    "proposition": "监管机构应具备充分的权力、资源和独立性以监督合规、实施检查和制裁。",
    "source_quotes": [
      "Supervisors should have sufficient authority, resources, and independence to monitor compliance, conduct inspections, and impose sanctions."
    ],
    "relation_cues": [
      "should",
      "have"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "监管机构履行职责"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "赋予监管机构充足的权力、资源和独立性",
      "outcomes_or_paths": [
        "监督合规、实施检查、实施制裁"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001372",
        "quote": "Supervisors should have sufficient authority, resources, and independence to monitor compliance, conduct inspections, and impose sanctions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N001373"
    ],
    "proposition": "各辖区应对指定非金融行业和职业（DNFBP）实施许可、注册和监管。",
    "source_quotes": [
      "Jurisdictions should subject DNFBPs to licensing, registration, and supervision by competent authorities or self-regulatory bodies."
    ],
    "relation_cues": [
      "should",
      "subject to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "指定非金融行业和职业"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "对DNFBP实施许可、注册和监管",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001373",
        "quote": "Jurisdictions should subject DNFBPs to licensing, registration, and supervision by competent authorities or self-regulatory bodies."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N001374"
    ],
    "proposition": "各辖区应设立金融情报机构（FIU）以分析可疑交易报告并支持执法调查。",
    "source_quotes": [
      "Jurisdictions should establish an FIU to analyze suspicious transaction reports and support law enforcement investigations."
    ],
    "relation_cues": [
      "should",
      "establish"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "可疑交易报告分析"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "设立FIU以分析可疑交易报告并支持执法调查",
      "outcomes_or_paths": [
        "支持执法调查"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001374",
        "quote": "Jurisdictions should establish an FIU to analyze suspicious transaction reports and support law enforcement investigations."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_008",
    "unit_ids": [
      "v7u_N001375"
    ],
    "proposition": "主管机关应有权追踪、冻结和扣押犯罪资产，实施跨境货币管制，并收集AML/CFT统计数据。",
    "source_quotes": [
      "Authorities should have powers to track, freeze, and seize criminal assets, enforce cross-border currency controls, and collect AML/CFT statistics."
    ],
    "relation_cues": [
      "should",
      "have powers"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "犯罪资产和跨境货币"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "授予主管机关追踪、冻结、扣押资产等权力",
      "outcomes_or_paths": [
        "实施跨境货币管制，收集统计"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001375",
        "quote": "Authorities should have powers to track, freeze, and seize criminal assets, enforce cross-border currency controls, and collect AML/CFT statistics."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_009",
    "unit_ids": [
      "v7u_N001376"
    ],
    "proposition": "各辖区应制定明确的指引、反馈和相称的制裁以确保合规与执行。",
    "source_quotes": [
      "Jurisdictions should have clear guidelines, feedback, and proportionate sanctions in place to ensure compliance and enforcement."
    ],
    "relation_cues": [
      "should",
      "have"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "合规与执行"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "制定指引、反馈和制裁",
      "outcomes_or_paths": [
        "确保合规与执行"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001376",
        "quote": "Jurisdictions should have clear guidelines, feedback, and proportionate sanctions in place to ensure compliance and enforcement."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_010",
    "unit_ids": [
      "v7u_N001377"
    ],
    "proposition": "各辖区应迅速采纳并全面实施维也纳、巴勒莫和反恐融资公约及其他相关国际协议。",
    "source_quotes": [
      "Recommendations 36 to 40 advise jurisdictions to swiftly adopt and fully implement the Vienna, Palermo, and Terrorist Financing Conventions, along with other relevant international agreements."
    ],
    "relation_cues": [
      "advise",
      "adopt",
      "implement"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "国际公约和协议"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "采纳并实施相关国际公约",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001377",
        "quote": "Recommendations 36 to 40 advise jurisdictions to swiftly adopt and fully implement the Vienna, Palermo, and Terrorist Financing Conventions, along with other relevant international agreements."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_011",
    "unit_ids": [
      "v7u_N001378"
    ],
    "proposition": "各辖区应为洗钱和恐怖融资案件提供广泛的司法协助，确保高效处理请求。",
    "source_quotes": [
      "Jurisdictions should provide broad mutual legal assistance for money laundering and terrorist financing cases, ensuring efficient processes for handling such requests."
    ],
    "relation_cues": [
      "should",
      "provide",
      "ensuring"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "洗钱和恐怖融资案件"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "提供广泛司法协助",
      "outcomes_or_paths": [
        "高效处理请求"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001378",
        "quote": "Jurisdictions should provide broad mutual legal assistance for money laundering and terrorist financing cases, ensuring efficient processes for handling such requests."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_012",
    "unit_ids": [
      "v7u_N001379"
    ],
    "proposition": "各辖区应应外国当局请求，迅速行动识别、冻结、扣押和没收犯罪资产。",
    "source_quotes": [
      "Jurisdictions should take rapid action to identify, freeze, seize, and confiscate criminal assets at the request of foreign authorities."
    ],
    "relation_cues": [
      "should",
      "take action",
      "at the request of"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "外国当局请求"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "识别、冻结、扣押、没收犯罪资产",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001379",
        "quote": "Jurisdictions should take rapid action to identify, freeze, seize, and confiscate criminal assets at the request of foreign authorities."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_013",
    "unit_ids": [
      "v7u_N001380"
    ],
    "proposition": "各辖区应确保对洗钱和恐怖融资进行引渡，包括在无法引渡时起诉本国国民。",
    "source_quotes": [
      "Additionally, they should ensure extradition for money laundering and terrorist financing, including prosecuting nationals if extradition is not possible."
    ],
    "relation_cues": [
      "should",
      "ensure",
      "including",
      "if"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "洗钱和恐怖融资案件"
      ],
      "basis_or_condition": [
        "无法引渡"
      ],
      "focal_handling_or_judgment": "确保引渡或起诉",
      "outcomes_or_paths": [
        "引渡成功",
        "无法引渡时起诉本国国民"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001380",
        "quote": "Additionally, they should ensure extradition for money laundering and terrorist financing, including prosecuting nationals if extradition is not possible."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_014",
    "unit_ids": [
      "v7u_N001381"
    ],
    "proposition": "当局应通过信息交换和联合调查促进国际合作以有效打击全球金融犯罪。",
    "source_quotes": [
      "Authorities should facilitate international cooperation through information exchange and joint investigations to combat financial crimes effectively on a global scale."
    ],
    "relation_cues": [
      "should",
      "facilitate",
      "through"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "打击全球金融犯罪"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "通过信息交换和联合调查促进国际合作",
      "outcomes_or_paths": [
        "有效打击金融犯罪"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001381",
        "quote": "Authorities should facilitate international cooperation through information exchange and joint investigations to combat financial crimes effectively on a global scale."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
