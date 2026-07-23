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

section_id: `CH31-S01`

section_title: `Cooperation between authorities > Roles of regulators, law enforcement, and FIUs`

section_text_with_unit_anchors:

```text
[v7u_N002207|2207] A regulator’s role is to set detailed rules, ensure they are followed, and ensure that the preventative controls in the private sector are effective.
ZH: 监管机构的职责是制定详细规则、确保遵守并保证私营部门预防性控制有效

[v7u_N002208|2208] Regulators authorize regulated businesses via licenses and registrations and then undertake risk-based supervision of these organizations to ensure compliance and identify noncompliance.
ZH: 监管机构通过许可和注册授权受监管实体，并开展风险为本的监督

[v7u_N002209|2209] Regulators have a range of tools to ensure compliance, up to and including issuing fines and enforcement actions for serious cases.
ZH: 监管机构拥有多种合规工具，包括罚款和执法行动

[v7u_N002210|2210] Law enforcement undertakes investigations to bring money launderers to justice, take away their assets, and achieve other disruptive effects.
ZH: 执法部门开展调查以将洗钱者绳之以法并没收资产

[v7u_N002211|2211] Law enforcement investigators work with prosecution authorities to bring court proceedings.
ZH: 执法调查人员与检察机关合作提起刑事诉讼

[v7u_N002212|2212] The relationship between law enforcement and prosecution authorities varies significantly between jurisdictions, depending on the legal system in each jurisdiction.
ZH: 执法与检察机关的关系因司法管辖区法律体系而异

[v7u_N002213|2213] Asset recovery is an important part of AML/CFT systems. Law enforcement and prosecution authorities use asset recovery as a mechanism to ensure that crime does not pay.
ZH: 资产追缴是反洗钱/反恐怖融资体系的重要组成部分，确保犯罪无利可图

[v7u_N002214|2214] Depending on their location, law enforcement agencies have varying scopes of authority for addressing different types of crime.
ZH: 执法机构的权限范围因所在地和犯罪类型而异

[v7u_N002215|2215] For example, local police have different responsibilities compared to national or federal agencies.
ZH: 例如地方警察与国家级或联邦机构的职责不同

[v7u_N002216|2216] Some law enforcement agencies might also have other responsibilities.
ZH: 部分执法机构可能还承担其他职责

[v7u_N002217|2217] For example, tax authorities can be responsible for investigating tax crime as well as setting tax policy.
ZH: 例如税务机关既负责调查税务犯罪也负责制定税收政策

[v7u_N002218|2218] National FIUs receive, analyze, and disseminate financial intelligence.
ZH: 国家金融情报机构接收、分析和传播金融情报

[v7u_N002219|2219] They produce strategic analysis that is used to understand trends, typologies, and threats.
ZH: FIU开展战略分析以了解趋势、类型和威胁

[v7u_N002220|2220] They also produce operational analysis that law enforcement uses to investigate and disrupt money laundering, terrorist financing, and predicate offenses.
ZH: FIU开展操作分析供执法部门调查洗钱、恐怖融资和上游犯罪

[v7u_N002221|2221] In some cases, the same organization can be both a regulator and an FIU, and FIUs can also be part of law enforcement agencies.
ZH: 同一机构可同时承担监管机构、金融情报机构和执法机构的角色

[v7u_N002222|2222] There are many different models, but the main point is that the agencies cooperate and share information when it pertains to each other’s functions.
ZH: 各机构必须合作并共享与各自职能相关的信息

[v7u_N002223|2223] These agencies should also share information with their international counterparts to handle crossborder money laundering and terrorist financing.
ZH: 机构应与国际同行共享信息以打击跨境洗钱和恐怖融资

[v7u_N002224|2224] There are various channels for information sharing, depending on whether it is intelligence, evidence, or regulatory information.
ZH: 信息共享渠道因信息类型（情报、证据或监管信息）而异
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002208"
    ],
    "proposition": "监管机构通过许可和注册授权受监管实体，并开展风险为本的监督以确保合规和发现不合规。",
    "source_quotes": [
      "Regulators authorize regulated businesses via licenses and registrations and then undertake risk-based supervision of these organizations to ensure compliance and identify noncompliance."
    ],
    "relation_cues": [
      "authorize",
      "risk-based supervision",
      "ensure compliance",
      "identify noncompliance"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "通过许可和注册授权受监管实体"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "开展风险为本的监督",
      "outcomes_or_paths": [
        "确保合规",
        "发现不合规"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002208",
        "quote": "Regulators authorize regulated businesses via licenses and registrations and then undertake risk-based supervision of these organizations to ensure compliance and identify noncompliance."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002210"
    ],
    "proposition": "执法部门开展调查以将洗钱者绳之以法、没收资产并实现其他破坏性效果。",
    "source_quotes": [
      "Law enforcement undertakes investigations to bring money launderers to justice, take away their assets, and achieve other disruptive effects."
    ],
    "relation_cues": [
      "investigations",
      "bring to justice",
      "take away assets",
      "disruptive effects"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "开展调查",
      "outcomes_or_paths": [
        "将洗钱者绳之以法",
        "没收资产",
        "实现其他破坏性效果"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002210",
        "quote": "Law enforcement undertakes investigations to bring money launderers to justice, take away their assets, and achieve other disruptive effects."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002211"
    ],
    "proposition": "执法调查人员与检察机关合作提起刑事诉讼。",
    "source_quotes": [
      "Law enforcement investigators work with prosecution authorities to bring court proceedings."
    ],
    "relation_cues": [
      "work with",
      "bring court proceedings"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "与检察机关合作提起刑事诉讼",
      "outcomes_or_paths": [
        "提起刑事诉讼"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002211",
        "quote": "Law enforcement investigators work with prosecution authorities to bring court proceedings."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002218",
      "v7u_N002219",
      "v7u_N002220"
    ],
    "proposition": "国家金融情报机构接收、分析和传播金融情报，并产生战略分析和操作分析，分别用于了解趋势、类型和威胁，以及供执法部门调查和打击犯罪。",
    "source_quotes": [
      "National FIUs receive, analyze, and disseminate financial intelligence.",
      "They produce strategic analysis that is used to understand trends, typologies, and threats.",
      "They also produce operational analysis that law enforcement uses to investigate and disrupt money laundering, terrorist financing, and predicate offenses."
    ],
    "relation_cues": [
      "receive",
      "analyze",
      "disseminate",
      "produce strategic analysis",
      "produce operational analysis"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "接收金融情报"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "分析和传播金融情报，并产生战略分析和操作分析",
      "outcomes_or_paths": [
        "了解趋势、类型和威胁",
        "供执法部门调查和打击洗钱、恐怖融资及上游犯罪"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002218",
        "quote": "National FIUs receive, analyze, and disseminate financial intelligence."
      },
      {
        "unit_id": "v7u_N002219",
        "quote": "They produce strategic analysis that is used to understand trends, typologies, and threats."
      },
      {
        "unit_id": "v7u_N002220",
        "quote": "They also produce operational analysis that law enforcement uses to investigate and disrupt money laundering, terrorist financing, and predicate offenses."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002222"
    ],
    "proposition": "各机构必须在信息涉及各自职能时合作并共享信息。",
    "source_quotes": [
      "There are many different models, but the main point is that the agencies cooperate and share information when it pertains to each other’s functions."
    ],
    "relation_cues": [
      "cooperate",
      "share information",
      "when it pertains"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "信息涉及各自职能时"
      ],
      "focal_handling_or_judgment": "机构之间合作并共享信息",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002222",
        "quote": "There are many different models, but the main point is that the agencies cooperate and share information when it pertains to each other’s functions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N002223"
    ],
    "proposition": "机构应与国际同行共享信息以打击跨境洗钱和恐怖融资。",
    "source_quotes": [
      "These agencies should also share information with their international counterparts to handle crossborder money laundering and terrorist financing."
    ],
    "relation_cues": [
      "share information",
      "to handle crossborder money laundering"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "与国际同行共享信息",
      "outcomes_or_paths": [
        "打击跨境洗钱和恐怖融资"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002223",
        "quote": "These agencies should also share information with their international counterparts to handle crossborder money laundering and terrorist financing."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
