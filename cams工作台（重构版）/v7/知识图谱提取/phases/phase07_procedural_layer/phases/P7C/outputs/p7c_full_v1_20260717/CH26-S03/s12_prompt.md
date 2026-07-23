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

section_id: `CH26-S03`

section_title: `Other laws and regulations that impact organizations > EU General Data Protection Regulation`

section_text_with_unit_anchors:

```text
[v7u_N002042|2042] The General Data Protection Regulation (GDPR) is a law the EU has adopted to safeguard the privacy and data protection rights of individuals living in its jurisdiction.
ZH: 《通用数据保护条例》是欧盟为保护个人隐私和数据权利而通过的法律

[v7u_N002043|2043] Unlike directives, the GDPR is a legislative act that applies directly and uniformly across all member states without a need for national legislation.
ZH: 《通用数据保护条例》作为法规直接适用于所有成员国，无需转化为国内法

[v7u_N002044|2044] The GDPR builds upon previous EU privacy and data protection law through its legal structure, scope, accountability requirements, and enforcement mechanisms.
ZH: 《通用数据保护条例》在原有欧盟隐私和数据保护法律基础上构建

[v7u_N002045|2045] The EU extended the GDPR to apply to the entire EEA, which consists of the EU member states plus Norway, Iceland, and Liechtenstein, through procedures established between the EU and EEA.
ZH: 《通用数据保护条例》通过欧盟与欧洲经济区的程序扩展适用于整个欧洲经济区

[v7u_N002046|2046] To fall within the scope of the GDPR, an organization must fall into one of two categories: the organization is established in the EU and EEA, or offers goods or services to, or monitors the behavior of, data subjects in the EU and EEA.
ZH: 《通用数据保护条例》适用范围：在欧盟/欧洲经济区设立，或向该区域数据主体提供商品/服务或监控其行为

[v7u_N002047|2047] If the organization is established in the EU and EEA, it must apply GDPR rights and protections to the personal data of data subjects irrespective of their location.
ZH: 在欧盟/欧洲经济区设立的组织，无论数据主体位于何处，均须适用《通用数据保护条例》

[v7u_N002048|2048] If the organization is not established in the EU or EEA, it is required to apply GDPR rights and protections to the personal data of data subjects located in the EU and EEA.
ZH: 非欧盟/欧洲经济区组织须对位于欧盟/欧洲经济区的数据主体适用《通用数据保护条例》

[v7u_N002049|2049] The regulation clearly defines data collectors and data processors, who have different duties in handling personal data.
ZH: 《通用数据保护条例》明确区分数据控制者和数据处理者，二者承担不同职责

[v7u_N002050|2050] Key provisions of the GDPR include the following:
ZH: 《通用数据保护条例》的主要条款包括以下内容

[v7u_N002051|2051] Strengthen data protection rights: Individuals, or data subjects, have rights regarding the use of their personal data, including access, correction, deletion, portability, and rectification.
ZH: 《通用数据保护条例》加强数据主体权利，包括访问、更正、删除、可携带和纠正权

[v7u_N002052|2052] Implement strict cross-border transfer requirements: Data transfer mechanisms must be in place when there is a transfer of personal data outside the EU and EEA to a jurisdiction whose data protection practices have been deemed inadequate by the European Commission.
ZH: 《通用数据保护条例》要求对向欧盟/欧洲经济区外保护不足的司法管辖区传输个人数据实施严格跨境传输要求

[v7u_N002053|2053] Increase accountability of in-scope organizations: Organizations are required to notify the relevant supervisory authority of a breach without undue delay, appoint a data protection office in certain circumstances, create and maintain appropriate data protection impact assessments.
ZH: 《通用数据保护条例》要求组织及时通知监管机构数据泄露、指定数据保护官并进行数据保护影响评估

[v7u_N002054|2054] Introduce a two-tier fining system that is based on types of infringement: Less serious infringements result in lower fines; these include any violation of the articles governing controllers and processors, certification bodies, and monitoring bodies. More serious infringements result in higher fines; these include violations of articles governing key principles of the right to privacy and the right to be forgotten.
ZH: 《通用数据保护条例》引入基于侵权类型的两级罚款制度，严重侵权罚款更高

[v7u_N002055|2055] Modernize the approach to privacy and personal data protection: The GDPR's intent is to be technology-neutral, meaning it applies to the processing of personal data regardless of the specific technology that organizations use.
ZH: 《通用数据保护条例》旨在技术中立，适用于任何技术下的个人数据处理

[v7u_N002056|2056] Provide lawful reasons for obtaining and processing personal data: Organizations must inform data subjects that one or more of the following lawful reasons exist: consent, contractual obligation, legal obligation, public interest, vital interests, or legitimate interests.
ZH: 《通用数据保护条例》要求组织告知数据主体处理个人数据的合法理由，如同意、合同义务等
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002046",
      "v7u_N002047",
      "v7u_N002048"
    ],
    "proposition": "组织是否属于GDPR适用范围取决于其是否在EU/EEA设立或向EU/EEA数据主体提供商品/服务或监控其行为；在EU/EEA设立的组织须对所有数据主体适用GDPR，非设立组织须对位于EU/EEA的数据主体适用GDPR。",
    "source_quotes": [
      "To fall within the scope of the GDPR, an organization must fall into one of two categories: the organization is established in the EU and EEA, or offers goods or services to, or monitors the behavior of, data subjects in the EU and EEA.",
      "If the organization is established in the EU and EEA, it must apply GDPR rights and protections to the personal data of data subjects irrespective of their location.",
      "If the organization is not established in the EU or EEA, it is required to apply GDPR rights and protections to the personal data of data subjects located in the EU and EEA."
    ],
    "relation_cues": [
      "must fall into",
      "if",
      "must apply",
      "required to apply"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "需要判断组织是否受GDPR约束"
      ],
      "basis_or_condition": [
        "组织在EU/EEA设立",
        "组织向EU/EEA数据主体提供商品/服务或监控其行为"
      ],
      "focal_handling_or_judgment": "确定GDPR适用范围",
      "outcomes_or_paths": [
        "若在EU/EEA设立，则全面适用GDPR",
        "若未在EU/EEA设立但向EU/EEA数据主体提供商品/服务或监控其行为，则仅对位于EU/EEA的数据主体适用GDPR"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002046",
        "quote": "To fall within the scope of the GDPR, an organization must fall into one of two categories: the organization is established in the EU and EEA, or offers goods or services to, or monitors the behavior of, data subjects in the EU and EEA."
      },
      {
        "unit_id": "v7u_N002047",
        "quote": "If the organization is established in the EU and EEA, it must apply GDPR rights and protections to the personal data of data subjects irrespective of their location."
      },
      {
        "unit_id": "v7u_N002048",
        "quote": "If the organization is not established in the EU or EEA, it is required to apply GDPR rights and protections to the personal data of data subjects located in the EU and EEA."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002052"
    ],
    "proposition": "向EU/EEA外保护不足的司法管辖区传输个人数据时，必须实施数据传输机制。",
    "source_quotes": [
      "Data transfer mechanisms must be in place when there is a transfer of personal data outside the EU and EEA to a jurisdiction whose data protection practices have been deemed inadequate by the European Commission."
    ],
    "relation_cues": [
      "must be in place",
      "when"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "向EU/EEA外保护不足的司法管辖区传输个人数据"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "实施数据传输机制",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002052",
        "quote": "Data transfer mechanisms must be in place when there is a transfer of personal data outside the EU and EEA to a jurisdiction whose data protection practices have been deemed inadequate by the European Commission."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002053"
    ],
    "proposition": "在GDPR范围内的组织须通知监管机构数据泄露、指定数据保护官并进行数据保护影响评估。",
    "source_quotes": [
      "Organizations are required to notify the relevant supervisory authority of a breach without undue delay, appoint a data protection office in certain circumstances, create and maintain appropriate data protection impact assessments."
    ],
    "relation_cues": [
      "required to"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "履行数据保护义务",
      "outcomes_or_paths": [
        "通知监管机构数据泄露",
        "指定数据保护官",
        "进行数据保护影响评估"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002053",
        "quote": "Organizations are required to notify the relevant supervisory authority of a breach without undue delay, appoint a data protection office in certain circumstances, create and maintain appropriate data protection impact assessments."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002054"
    ],
    "proposition": "根据侵权类型分为较不严重和较严重，分别处以较低或较高罚款。",
    "source_quotes": [
      "Less serious infringements result in lower fines; these include any violation of the articles governing controllers and processors, certification bodies, and monitoring bodies. More serious infringements result in higher fines; these include violations of articles governing key principles of the right to privacy and the right to be forgotten."
    ],
    "relation_cues": [
      "result in"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "发生侵权"
      ],
      "basis_or_condition": [
        "侵权类型：较不严重或较严重"
      ],
      "focal_handling_or_judgment": "确定罚款级别",
      "outcomes_or_paths": [
        "较不严重：较低罚款",
        "较严重：较高罚款"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002054",
        "quote": "Less serious infringements result in lower fines; these include any violation of the articles governing controllers and processors, certification bodies, and monitoring bodies. More serious infringements result in higher fines; these include violations of articles governing key principles of the right to privacy and the right to be forgotten."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002056"
    ],
    "proposition": "组织必须告知数据主体处理个人数据的合法理由（如同意、合同义务等）。",
    "source_quotes": [
      "Organizations must inform data subjects that one or more of the following lawful reasons exist: consent, contractual obligation, legal obligation, public interest, vital interests, or legitimate interests."
    ],
    "relation_cues": [
      "must inform"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织处理个人数据"
      ],
      "basis_or_condition": [
        "存在合法理由之一"
      ],
      "focal_handling_or_judgment": "告知数据主体合法理由",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002056",
        "quote": "Organizations must inform data subjects that one or more of the following lawful reasons exist: consent, contractual obligation, legal obligation, public interest, vital interests, or legitimate interests."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
