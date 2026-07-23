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

section_id: `CH04-S02`

section_title: `Consequences of financial crime > Institutional accountability to prevent financial crime`

section_text_with_unit_anchors:

```text
[v7u_N000321|321] Financial crime undermines economic stability and has wider negative societal consequences if ignored.
ZH: 金融犯罪破坏经济稳定并带来负面社会后果。

[v7u_N000322|322] Imposing strict obligations through legislation and regulation on institutions with the objective of preventing illicit funds entering and flowing through the financial system is one of the ways to fight financial crime.
ZH: 通过立法和监管对机构施加义务是打击金融犯罪的方式之一。

[v7u_N000323|323] Depending upon the entity type, how regulation is applied can differ greatly due to the distinct differences between regulated entities and obliged entities.
ZH: 受监管实体与义务实体因类型不同，监管适用方式差异很大。

[v7u_N000324|324] A regulated entity is a business that falls under the direct supervision of financial regulators, such as banks, money services businesses, and other financial institutions.
ZH: 受监管实体是直接受金融监管机构监督的企业，如银行、货币服务企业等。

[v7u_N000325|325] These entities must comply with detailed AML/CFT requirements which include, but are not limited to, implementing comprehensive AML programs, conducting customer due diligence, real-time transaction monitoring, and promptly reporting suspicious activity.
ZH: 受监管实体必须遵守详细的反洗钱/反恐怖融资要求，包括实施反洗钱计划、客户尽职调查、实时交易监控和可疑活动报告。

[v7u_N000326|326] An obliged entity is a broader category that includes both regulated entities and nonfinancial organizations subject to other financial crime laws, such as ABC and sanctions regulations.
ZH: 义务实体是更广泛的类别，包括受监管实体和受其他金融犯罪法律约束的非金融组织。

[v7u_N000327|327] For example, sectors like energy, mining, logistics, pharmaceuticals, and real estate might not be directly regulated by financial authorities, yet they must perform risk assessments and have adequate and effective controls to deter financial crime.
ZH: 非金融行业如能源、采矿、物流、制药和房地产等也须进行风险评估并采取控制措施。

[v7u_N000328|328] These organizations are expected to take reasonable steps to prevent illicit activities and to implement remediation measures following enforcement actions, such as fines or leadership changes.
ZH: 义务实体应采取合理措施预防非法活动，并在执法行动后实施补救措施。

[v7u_N000329|329] An entity can be both regulated and obliged, meaning all relevant financial crime laws and regulations will apply to the institution.
ZH: 一个实体可以同时是受监管实体和义务实体，适用所有相关金融犯罪法律。

[v7u_N000330|330] Regulatory developments, such as the AML Act in the US, the Economic Crime and Corporate Transparency Act 2023 in the UK, the EU AML Package, and updated guidelines from FATF, have heightened industry-wide standards.
ZH: 美国反洗钱法案、英国经济犯罪法案、欧盟反洗钱一揽子计划及FATF指南等监管发展提高了行业标准。

[v7u_N000331|331] Failure to comply with these obligations can result in severe consequences, including heavy fines, operational restrictions, and substantial reputational damage.
ZH: 不遵守义务可能导致巨额罚款、运营限制和声誉损害等严重后果。

[v7u_N000332|332] In extreme cases, repeat offenders risk disqualification from critical markets, loss of operating licenses, or entering into a deferred prosecution agreement whereby the offending entity agrees to fulfill certain requirements, such as an overhaul of the AML/CTF compliance program in exchange for the postponement of prosecution.
ZH: 屡犯者可能面临市场禁入、吊销执照或达成暂缓起诉协议。

[v7u_N000333|333] All institutions, irrespective of whether regulated or obliged, must invest in appropriate and effective compliance strategies, staff training, and advanced monitoring technologies to safeguard against financial crime in an increasingly complex environment. These measures not only protect the institution from regulatory scrutiny, but also safeguard consumers and investors, which builds confidence and supports long-term business sustainability.
ZH: 所有机构必须投资合规策略、员工培训和先进监控技术以防范金融犯罪。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N000325"
    ],
    "proposition": "受监管实体必须遵守详细的反洗钱/反恐怖融资要求，包括实施反洗钱计划、客户尽职调查、实时交易监控和可疑活动报告。",
    "source_quotes": [
      "These entities must comply with detailed AML/CFT requirements which include, but are not limited to, implementing comprehensive AML programs, conducting customer due diligence, real-time transaction monitoring, and promptly reporting suspicious activity."
    ],
    "relation_cues": [
      "must"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "实体是受监管实体"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "遵守详尽的AML/CFT要求",
      "outcomes_or_paths": [
        "实施AML程序、客户尽职调查、实时交易监控和可疑活动报告"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000325",
        "quote": "These entities must comply with detailed AML/CFT requirements which include, but are not limited to, implementing comprehensive AML programs, conducting customer due diligence, real-time transaction monitoring, and promptly reporting suspicious activity."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N000327"
    ],
    "proposition": "不受直接监管的实体（如能源、采矿等）必须进行风险评估并具备充分有效的控制措施以防范金融犯罪。",
    "source_quotes": [
      "For example, sectors like energy, mining, logistics, pharmaceuticals, and real estate might not be directly regulated by financial authorities, yet they must perform risk assessments and have adequate and effective controls to deter financial crime."
    ],
    "relation_cues": [
      "must"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "实体不受金融监管机构直接监管"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "进行风险评估并具备充分有效的控制措施",
      "outcomes_or_paths": [
        "防范金融犯罪"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000327",
        "quote": "For example, sectors like energy, mining, logistics, pharmaceuticals, and real estate might not be directly regulated by financial authorities, yet they must perform risk assessments and have adequate and effective controls to deter financial crime."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N000328"
    ],
    "proposition": "义务实体应采取合理步骤预防非法活动，并在执法行动后实施补救措施。",
    "source_quotes": [
      "These organizations are expected to take reasonable steps to prevent illicit activities and to implement remediation measures following enforcement actions, such as fines or leadership changes."
    ],
    "relation_cues": [
      "expected to"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "执法行动之后"
      ],
      "focal_handling_or_judgment": "采取合理步骤预防非法活动，并实施补救措施",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000328",
        "quote": "These organizations are expected to take reasonable steps to prevent illicit activities and to implement remediation measures following enforcement actions, such as fines or leadership changes."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N000331",
      "v7u_N000332"
    ],
    "proposition": "不遵守义务可能导致严重后果，包括罚款、运营限制和声誉损害；极端情况下，屡犯者还可能面临市场禁入、吊销执照或达成暂缓起诉协议（需满足合规改造要求）。",
    "source_quotes": [
      "Failure to comply with these obligations can result in severe consequences, including heavy fines, operational restrictions, and substantial reputational damage.",
      "In extreme cases, repeat offenders risk disqualification from critical markets, loss of operating licenses, or entering into a deferred prosecution agreement whereby the offending entity agrees to fulfill certain requirements, such as an overhaul of the AML/CTF compliance program in exchange for the postponement of prosecution."
    ],
    "relation_cues": [
      "can",
      "risk",
      "agrees to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "未遵守义务"
      ],
      "basis_or_condition": [
        "极端情况下",
        "屡犯者"
      ],
      "focal_handling_or_judgment": "导致严重后果",
      "outcomes_or_paths": [
        "巨额罚款、运营限制、声誉损害",
        "市场禁入、吊销执照",
        "达成暂缓起诉协议（需承诺全面整改AML/CTF合规计划）"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000331",
        "quote": "Failure to comply with these obligations can result in severe consequences, including heavy fines, operational restrictions, and substantial reputational damage."
      },
      {
        "unit_id": "v7u_N000332",
        "quote": "In extreme cases, repeat offenders risk disqualification from critical markets, loss of operating licenses, or entering into a deferred prosecution agreement whereby the offending entity agrees to fulfill certain requirements, such as an overhaul of the AML/CTF compliance program in exchange for the postponement of prosecution."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N000333"
    ],
    "proposition": "所有机构必须投资适当的合规策略、员工培训和先进监控技术以防范金融犯罪。这些措施不仅保护机构免受监管审查，还保障消费者和投资者，建立信心并支持长期业务可持续性。",
    "source_quotes": [
      "All institutions, irrespective of whether regulated or obliged, must invest in appropriate and effective compliance strategies, staff training, and advanced monitoring technologies to safeguard against financial crime in an increasingly complex environment. These measures not only protect the institution from regulatory scrutiny, but also safeguard consumers and investors, which builds confidence and supports long-term business sustainability."
    ],
    "relation_cues": [
      "must"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "投资合规策略、人员培训和先进监控技术",
      "outcomes_or_paths": [
        "防范金融犯罪",
        "保护机构免受监管审查",
        "保障消费者和投资者",
        "建立信心并支持长期业务可持续性"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N000333",
        "quote": "All institutions, irrespective of whether regulated or obliged, must invest in appropriate and effective compliance strategies, staff training, and advanced monitoring technologies to safeguard against financial crime in an increasingly complex environment. These measures not only protect the institution from regulatory scrutiny, but also safeguard consumers and investors, which builds confidence and supports long-term business sustainability."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
