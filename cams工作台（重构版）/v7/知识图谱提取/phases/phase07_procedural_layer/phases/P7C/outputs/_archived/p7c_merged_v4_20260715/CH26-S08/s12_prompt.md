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

section_id: `CH26-S08`

section_title: `Other laws and regulations that impact organizations > ESG regulations`

section_text_with_unit_anchors:

```text
[v7u_N002105|2105] “Environmental, social, and governance” (ESG) refers to a framework organizations use to steer their business practices in accordance with the objectives of sustainable development.
ZH: ESG框架定义：环境、社会和治理

[v7u_N002106|2106] “Environmental” refers to an organization’s impact on the planet.
ZH: ESG中“环境”指组织对地球的影响

[v7u_N002107|2107] “Social” refers to an organization’s relationship with various stakeholders, including employees, customers, and communities within which they operate.
ZH: ESG中“社会”指组织与利益相关者的关系

[v7u_N002108|2108] “Governance” refers to how factors such as leadership, board composition, and transparency govern an organization.
ZH: ESG中“治理”指领导力、董事会构成和透明度

[v7u_N002109|2109] The UN has established a number of initiatives to advance ESG goals on a global basis.
ZH: 联合国设立多项倡议推动全球ESG目标

[v7u_N002110|2110] A widely known initiative is its Sustainable Development Goals, which provide a framework of 17 objectives to address poverty, inequality, and environmental threats while promoting peace and prosperity.
ZH: 联合国可持续发展目标提供17项目标框架

[v7u_N002111|2111] All UN Member States adopted the goals, and many organizations align their strategies with them.
ZH: 所有联合国会员国采纳可持续发展目标

[v7u_N002112|2112] Other ESG-related UN initiatives include the UN Guiding Principles on Business and Human Rights, the UN Environment Program Finance Initiative, and the UN Global Compact, an initiative to encourage businesses to support a wide range of ESG priorities.
ZH: 其他ESG相关联合国倡议包括UNGP、UNEP FI和UNGC

[v7u_N002113|2113] Although ESG regulations vary across jurisdictions, trends include increased mandatory disclosure, accountability, and transparency in organizational practices. The scope of ESG ranges from climate change to corporate governance to human rights. ESG considerations intersect with AML/CFT with respect to:
ZH: ESG法规趋势与反洗钱/反恐怖融资交叉领域概述

[v7u_N002114|2114] Environmental crime: This includes, for example, noncompliance with antipollution rules to achieve economic benefits or the exploitation of illegal mining. Financial crime such as bribery and corruption of local officials might be involved as part of the enterprise.
ZH: 环境犯罪涉及违反环保规则和非法采矿，常伴随贿赂和腐败

[v7u_N002115|2115] Social impact: This includes the exploitation of forced labor and corruption to achieve business objectives.
ZH: 社会影响包括强迫劳动和腐败以实现商业目标

[v7u_N002116|2116] Governance and compliance: This includes governance failures that result in a failure to prevent financial crime within organizations; regulatory enforcement actions all over the world have demonstrated their impact.
ZH: 治理失败导致未能预防金融犯罪，全球监管执法行动已显示其影响

[v7u_N002117|2117] ESG and AML/CFT regulations are converging as global regulatory frameworks continue to evolve to include sustainable business practices and financial crime prevention.
ZH: ESG与反洗钱/反恐怖融资法规正趋于融合

[v7u_N002118|2118] Strong governance frameworks under ESG regulation help prevent and deter corruption, fraud, and other illicit financial activity.
ZH: ESG治理框架有助于预防和阻止腐败、欺诈等金融犯罪

[v7u_N002119|2119] In addition, ESG’s emphasis on social responsibility can help identify certain threats to human rights that might have links to financial crimes.
ZH: ESG社会责任有助于识别与金融犯罪相关的人权威胁

[v7u_N002120|2120] For example, money laundering often involves the proceeds of human trafficking and modern slavery.
ZH: 洗钱常涉及人口贩运和现代奴隶制的收益

[v7u_N002121|2121] By integrating ESG principles into AML/CFT compliance, organizations are better suited to identify and mitigate such risks.
ZH: 将ESG原则融入反洗钱/反恐怖融资合规有助于识别和缓解风险

[v7u_N002122|2122] Both ESG and AML/CFT compliance frameworks depend on a risk-based approach to enable effective compliance and risk mitigation.
ZH: ESG与反洗钱/反恐怖融资均依赖风险为本方法实现有效合规

[v7u_N002123|2123] For ESG regulation, organizations should identify, assess, and manage risks particular to the elements of ESG, such as environmental impact, social responsibility, and organizational governance integrity.
ZH: 组织应识别、评估和管理ESG相关风险，包括环境影响、社会责任和治理诚信

[v7u_N002124|2124] The risk-based approach helps organizations prioritize resources, focus, and efforts on high-risk areas, such as industries with very high carbon emissions or locations vulnerable to human rights violations.
ZH: 风险为本方法帮助组织将资源优先投入高风险领域，如高碳排放行业或人权风险地区

[v7u_N002125|2125] Similarly, AML/CFT regulations require organizations to assess and manage risks particular to money laundering and terrorist financing.
ZH: 反洗钱/反恐怖融资法规要求组织评估和管理洗钱与恐怖融资风险

[v7u_N002126|2126] The adoption of a risk-based approach enables organizations to prioritize resources on high-risk clients, jurisdictions, and services, ensuring that compliance levels are proportionate to the level of risk.
ZH: 采用风险为本方法使组织能够优先对高风险客户、司法管辖区和服务投入资源

[v7u_N002127|2127] Both ESG and AML/CFT frameworks require ongoing due diligence, monitoring, and responsiveness to emerging risks.
ZH: ESG与反洗钱/反恐怖融资框架均要求持续尽职调查、监控和应对新兴风险
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002118"
    ],
    "proposition": "强有力的ESG治理框架有助于预防和阻止腐败、欺诈和其他非法金融活动。",
    "source_quotes": [
      "Strong governance frameworks under ESG regulation help prevent and deter corruption, fraud, and other illicit financial activity."
    ],
    "relation_cues": [
      "help",
      "prevent",
      "deter"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "ESG法规下的强治理框架"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "预防和阻止腐败、欺诈和其他非法金融活动",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002118",
        "quote": "Strong governance frameworks under ESG regulation help prevent and deter corruption, fraud, and other illicit financial activity."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002119"
    ],
    "proposition": "ESG对社会责任的强调有助于识别可能与金融犯罪相关的人权威胁。",
    "source_quotes": [
      "In addition, ESG’s emphasis on social responsibility can help identify certain threats to human rights that might have links to financial crimes."
    ],
    "relation_cues": [
      "help",
      "identify",
      "might"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "ESG对社会责任的强调"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "识别可能与金融犯罪相关的人权威胁",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002119",
        "quote": "In addition, ESG’s emphasis on social responsibility can help identify certain threats to human rights that might have links to financial crimes."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002121"
    ],
    "proposition": "将ESG原则融入反洗钱/反恐怖融资合规后，组织能更好地识别和缓解此类风险。",
    "source_quotes": [
      "By integrating ESG principles into AML/CFT compliance, organizations are better suited to identify and mitigate such risks."
    ],
    "relation_cues": [
      "integrating",
      "better suited",
      "identify",
      "mitigate"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "将ESG原则融入反洗钱/反恐怖融资合规"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "组织能更好地识别和缓解风险",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002121",
        "quote": "By integrating ESG principles into AML/CFT compliance, organizations are better suited to identify and mitigate such risks."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002123"
    ],
    "proposition": "对于ESG法规，组织应识别、评估和管理ESG各要素（环境影响、社会责任和治理诚信）相关的风险。",
    "source_quotes": [
      "For ESG regulation, organizations should identify, assess, and manage risks particular to the elements of ESG, such as environmental impact, social responsibility, and organizational governance integrity."
    ],
    "relation_cues": [
      "should",
      "identify",
      "assess",
      "manage"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "ESG法规要求"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "组织应识别、评估和管理ESG相关风险",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002123",
        "quote": "For ESG regulation, organizations should identify, assess, and manage risks particular to the elements of ESG, such as environmental impact, social responsibility, and organizational governance integrity."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002125"
    ],
    "proposition": "同样，反洗钱/反恐怖融资法规要求组织评估和管理洗钱和恐怖融资特定风险。",
    "source_quotes": [
      "Similarly, AML/CFT regulations require organizations to assess and manage risks particular to money laundering and terrorist financing."
    ],
    "relation_cues": [
      "require",
      "assess",
      "manage"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "反洗钱/反恐怖融资法规要求"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "组织应评估和管理洗钱和恐怖融资风险",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002125",
        "quote": "Similarly, AML/CFT regulations require organizations to assess and manage risks particular to money laundering and terrorist financing."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N002127"
    ],
    "proposition": "ESG和反洗钱/反恐怖融资框架都要求持续尽职调查、监控和应对新兴风险。",
    "source_quotes": [
      "Both ESG and AML/CFT frameworks require ongoing due diligence, monitoring, and responsiveness to emerging risks."
    ],
    "relation_cues": [
      "require",
      "ongoing",
      "responsiveness"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "ESG和反洗钱/反恐怖融资框架"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "要求持续尽职调查、监控和应对新兴风险",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002127",
        "quote": "Both ESG and AML/CFT frameworks require ongoing due diligence, monitoring, and responsiveness to emerging risks."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
