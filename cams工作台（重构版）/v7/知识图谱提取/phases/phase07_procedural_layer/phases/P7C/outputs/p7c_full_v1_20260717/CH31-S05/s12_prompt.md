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

section_id: `CH31-S05`

section_title: `Cooperation between authorities > Law enforcement and FIU AFC cooperation`

section_text_with_unit_anchors:

```text
[v7u_N002250|2250] FATF requires that jurisdictions have FIUs to receive, analyze, and disseminate financial intelligence.
ZH: FATF要求各司法辖区设立FIU以接收、分析和传播金融情报

[v7u_N002251|2251] National FIUs produce strategic analysis, which looks at trends and patterns, and operational analysis, which focuses on specific targets.
ZH: 国家FIU开展战略分析和操作分析两种类型的情报分析

[v7u_N002252|2252] Operational analysis provides law enforcement with intelligence it can use for investigations into money laundering, terrorist financing, and predicate offenses. The intelligence can ultimately lead to disruptions, including arrests, prosecutions, convictions, and asset recovery.
ZH: 操作分析为执法部门提供可用于调查洗钱、恐怖融资和上游犯罪的情报

[v7u_N002253|2253] National FIUs disseminate intelligence packages to law enforcement based on their operational analysis.
ZH: 国家FIU根据操作分析向执法部门传播情报包

[v7u_N002254|2254] The level of analysis varies depending on the issue and the FIU.
ZH: 分析水平因问题和FIU而异

[v7u_N002255|2255] Sometimes FIUs undertake detailed work, checking multiple sources and applying a range of techniques. Sometimes the FIU disseminates intelligence that is less refined.
ZH: FIU传播的情报有时经过详细分析，有时较为粗略

[v7u_N002256|2256] For example, the FIU may choose to conduct limited additional checks on an urgent issue such as terrorism finance to disseminate information as quickly as possible.
ZH: 例如FIU对恐怖融资等紧急事项仅做有限检查以尽快传播信息

[v7u_N002257|2257] FIUs obtain SARs and other information from reporting entities and a range of other domestic sources. FIUs have access to other FIUs internationally.
ZH: FIU从报告实体、国内来源及其他国家FIU获取信息

[v7u_N002258|2258] Under FATF standards and principles set by the Egmont Group of FIUs, FIUs are expected to disseminate financial intelligence to each other, either spontaneously or on request.
ZH: 根据FATF标准和埃格蒙特集团原则，FIU应自发或应请求相互传播金融情报

[v7u_N002259|2259] FIUs can incorporate this data into operational analysis relating to cross-border money laundering and disseminate it to law enforcement for action.
ZH: FIU可将跨境数据纳入操作分析并传播给执法部门采取行动

[v7u_N002260|2260] Often, the material that FIUs disseminate to law enforcement is for intelligence use only, meaning that it usually cannot be used directly as evidence in court proceedings.
ZH: FIU向执法部门传播的材料通常仅供情报使用，不能直接作为法庭证据
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002250"
    ],
    "proposition": "FATF要求各司法辖区设立FIU，负责接收、分析和传播金融情报。",
    "source_quotes": [
      "FATF requires that jurisdictions have FIUs to receive, analyze, and disseminate financial intelligence."
    ],
    "relation_cues": [
      "requires"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FATF标准"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "司法辖区设立FIU并履行接收、分析和传播金融情报的职能",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002250",
        "quote": "FATF requires that jurisdictions have FIUs to receive, analyze, and disseminate financial intelligence."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002252",
      "v7u_N002253"
    ],
    "proposition": "FIU的操作分析为执法部门提供可用于调查的情报，并基于此传播情报包，最终可能导致逮捕、起诉、定罪和资产追回。",
    "source_quotes": [
      "Operational analysis provides law enforcement with intelligence it can use for investigations into money laundering, terrorist financing, and predicate offenses. The intelligence can ultimately lead to disruptions, including arrests, prosecutions, convictions, and asset recovery.",
      "National FIUs disseminate intelligence packages to law enforcement based on their operational analysis."
    ],
    "relation_cues": [
      "provides",
      "based on",
      "lead to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FIU开展操作分析"
      ],
      "basis_or_condition": [
        "操作分析结果"
      ],
      "focal_handling_or_judgment": "FIU向执法部门传播情报包",
      "outcomes_or_paths": [
        "执法部门用于调查洗钱、恐怖融资和上游犯罪",
        "可能导致逮捕、起诉、定罪和资产追回"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002252",
        "quote": "Operational analysis provides law enforcement with intelligence it can use for investigations into money laundering, terrorist financing, and predicate offenses. The intelligence can ultimately lead to disruptions, including arrests, prosecutions, convictions, and asset recovery."
      },
      {
        "unit_id": "v7u_N002253",
        "quote": "National FIUs disseminate intelligence packages to law enforcement based on their operational analysis."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002256"
    ],
    "proposition": "对于恐怖融资等紧急事项，FIU可能仅进行有限检查以尽快传播信息。",
    "source_quotes": [
      "For example, the FIU may choose to conduct limited additional checks on an urgent issue such as terrorism finance to disseminate information as quickly as possible."
    ],
    "relation_cues": [
      "for example",
      "may",
      "to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "紧急事项（如恐怖融资）"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "FIU选择进行有限检查",
      "outcomes_or_paths": [
        "尽快传播信息"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002256",
        "quote": "For example, the FIU may choose to conduct limited additional checks on an urgent issue such as terrorism finance to disseminate information as quickly as possible."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002258"
    ],
    "proposition": "根据FATF标准和埃格蒙特集团原则，FIU应自发或应请求相互传播金融情报。",
    "source_quotes": [
      "Under FATF standards and principles set by the Egmont Group of FIUs, FIUs are expected to disseminate financial intelligence to each other, either spontaneously or on request."
    ],
    "relation_cues": [
      "under",
      "expected to",
      "either or"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FATF标准和埃格蒙特集团原则"
      ],
      "basis_or_condition": [
        "自发或应请求"
      ],
      "focal_handling_or_judgment": "FIU相互传播金融情报",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002258",
        "quote": "Under FATF standards and principles set by the Egmont Group of FIUs, FIUs are expected to disseminate financial intelligence to each other, either spontaneously or on request."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002259"
    ],
    "proposition": "FIU可将从其他FIU获取的跨境数据纳入操作分析，并传播给执法部门采取行动。",
    "source_quotes": [
      "FIUs can incorporate this data into operational analysis relating to cross-border money laundering and disseminate it to law enforcement for action."
    ],
    "relation_cues": [
      "can",
      "incorporate into",
      "and"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FIU从其他FIU获取跨境数据"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "将数据纳入操作分析",
      "outcomes_or_paths": [
        "向执法部门传播并采取行动"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002259",
        "quote": "FIUs can incorporate this data into operational analysis relating to cross-border money laundering and disseminate it to law enforcement for action."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N002260"
    ],
    "proposition": "FIU向执法部门传播的材料通常仅供情报使用，不能直接作为法庭证据。",
    "source_quotes": [
      "Often, the material that FIUs disseminate to law enforcement is for intelligence use only, meaning that it usually cannot be used directly as evidence in court proceedings."
    ],
    "relation_cues": [
      "often",
      "meaning that",
      "cannot"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "FIU向执法部门传播材料"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "材料仅供情报使用，不能直接作为证据",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002260",
        "quote": "Often, the material that FIUs disseminate to law enforcement is for intelligence use only, meaning that it usually cannot be used directly as evidence in court proceedings."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
