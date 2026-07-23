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

section_id: `CH41-S08`

section_title: `Governance and oversight > • United Kingdom:`

section_text_with_unit_anchors:

```text
[v7u_N002978|2978] REP-CRIM report: Describes criminal activities detected within the financial institution.
ZH: REP-CRIM报告描述金融机构内检测到的犯罪活动。

[v7u_N002979|2979] Annual MLRO’s report: Summarizes the organization’s AFC compliance activities, highlighting trends, risks, and mitigation measures.
ZH: 年度MLRO报告总结组织的金融犯罪防控合规活动，突出趋势、风险和缓解措施。

[v7u_N002980|2980] Regulatory reporting requirements include, but are not limited to:
ZH: 监管报告要求的列表引导。

[v7u_N002981|2981] Accuracy and completeness: Reports must contain detailed, verifiable data to prevent errors, regulatory scrutiny, and reporting breaches.
ZH: 可疑活动报告必须包含详细、可验证的数据，以防止错误、监管审查和报告违规。

[v7u_N002982|2982] Timeliness: Filing deadlines differ globally, and institutions must ensure swift and precise submission.
ZH: 全球提交截止日期不同，机构必须确保及时、准确地提交报告。

[v7u_N002983|2983] Confidentiality and anti-tipping off: Disclosure of SAR details is strictly prohibited to prevent interference with law enforcement investigations.
ZH: 严格禁止泄露可疑活动报告细节，以防止干扰执法调查。

[v7u_N002984|2984] By aligning regulatory reporting processes with jurisdictional requirements, institutions strengthen financial integrity, regulatory cooperation, and financial crime prevention efforts.
ZH: 使监管报告流程符合司法管辖区要求，可增强金融诚信、监管合作和金融犯罪预防。

[v7u_N002985|2985] Responding to regulator requests is a crucial element of an organization’s AFC compliance program, underscoring the need for transparency, collaboration, and accountability. Effective engagement with regulators helps to avoid penalties, while demonstrating a culture of compliance that fosters long-term trust and credibility. It is also a key part of the cooperative effort between regulators and industry to combat money laundering, terrorism financing, and other financial crimes.
ZH: 回应监管机构请求是金融犯罪防控合规计划的关键要素，有助于避免处罚并建立信任。

[v7u_N002986|2986] Regulators may conduct routine examinations or targeted investigations, assessing whether institutions adhere to local and global AFC mandates.
ZH: 监管机构可能进行常规检查或专项调查，评估机构是否遵守当地和全球金融犯罪防控规定。

[v7u_N002987|2987] In some cases, a monitorship may be imposed following serious compliance breaches, requiring the institution to correct shortcomings under strict regulatory supervision.
ZH: 严重合规违规后可能实施监管监督，要求机构在严格监管下纠正缺陷。

[v7u_N002988|2988] By cooperating fully and addressing identified gaps promptly, organizations reduce reputational and operational risks.
ZH: 机构应充分合作并及时解决已发现的差距，以降低声誉和运营风险。

[v7u_N002989|2989] Jurisdictions often grant regulators special provisions to obtain relevant records and information. For example, in the UK, Section 166 of the Financial Services and Markets Act 2000 allows regulators to demand data on customer files, transactions, or risk management processes.
ZH: 英国《2000年金融服务与市场法》第166条允许监管机构要求提供客户档案、交易或风险管理流程数据。

[v7u_N002990|2990] Organizations must maintain accurate records and structured governance to quickly comply with such requests and demonstrate robust AFC controls.
ZH: 机构必须维护准确记录和结构化治理，以快速响应监管请求并展示有效的金融犯罪防控控制。

[v7u_N002991|2991] Best practices for engaging with regulators include the following:
ZH: 与监管机构互动的最佳实践包括以下内容。

[v7u_N002992|2992] Preparedness and data integrity: Keep customer due diligence files, transaction logs, and audit trails up to date, facilitating timely and accurate submissions.
ZH: 保持客户尽职调查文件、交易日志和审计线索最新，以便及时准确提交。

[v7u_N002993|2993] Designated liaison: Centralize regulator interactions under a head of compliance or similar role, ensuring efficient and consistent communication.
ZH: 指定合规负责人等角色集中处理监管互动，确保沟通高效一致。

[v7u_N002994|2994] Timely and transparent responses: Provide complete information before deadlines, proactively disclosing potential delays or challenges to build regulatory trust.
ZH: 在截止日期前提供完整信息，主动披露潜在延迟或挑战，以建立监管信任。

[v7u_N002995|2995] Remediation and monitoring: Develop corrective action plans, report progress, and strengthen AFC frameworks to prevent repeat findings.
ZH: 制定纠正行动计划、报告进展并加强金融犯罪防控框架，防止问题再次发生。

[v7u_N002996|2996] By responding promptly to regulator requests, organizations reinforce AFC commitments, mitigate compliance risks, and maintain strong supervisory relationships that bolster financial integrity.
ZH: 及时回应监管请求可强化金融犯罪防控承诺，降低合规风险并维护良好的监管关系。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002986"
    ],
    "proposition": "监管机构可能进行常规检查或专项调查，评估机构是否遵守当地和全球金融犯罪防控规定。",
    "source_quotes": [
      "Regulators may conduct routine examinations or targeted investigations, assessing whether institutions adhere to local and global AFC mandates."
    ],
    "relation_cues": [
      "may",
      "assessing"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "监管机构进行常规检查或专项调查"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "评估机构是否遵守当地和全球金融犯罪防控规定",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002986",
        "quote": "Regulators may conduct routine examinations or targeted investigations, assessing whether institutions adhere to local and global AFC mandates."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002987"
    ],
    "proposition": "严重合规违规后可能实施监管监督，要求机构在严格监管下纠正缺陷。",
    "source_quotes": [
      "In some cases, a monitorship may be imposed following serious compliance breaches, requiring the institution to correct shortcomings under strict regulatory supervision."
    ],
    "relation_cues": [
      "following",
      "may",
      "requiring"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "严重合规违规"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "可能实施监管监督(monitorship)",
      "outcomes_or_paths": [
        "机构在严格监管下纠正缺陷"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002987",
        "quote": "In some cases, a monitorship may be imposed following serious compliance breaches, requiring the institution to correct shortcomings under strict regulatory supervision."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002988"
    ],
    "proposition": "机构充分合作并及时解决已发现的差距，以降低声誉和运营风险。",
    "source_quotes": [
      "By cooperating fully and addressing identified gaps promptly, organizations reduce reputational and operational risks."
    ],
    "relation_cues": [
      "by",
      "reduce"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "机构充分合作并及时解决已发现的差距"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "降低声誉和运营风险",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002988",
        "quote": "By cooperating fully and addressing identified gaps promptly, organizations reduce reputational and operational risks."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002989"
    ],
    "proposition": "英国《2000年金融服务与市场法》第166条允许监管机构要求提供客户档案、交易或风险管理流程数据。",
    "source_quotes": [
      "Jurisdictions often grant regulators special provisions to obtain relevant records and information. For example, in the UK, Section 166 of the Financial Services and Markets Act 2000 allows regulators to demand data on customer files, transactions, or risk management processes."
    ],
    "relation_cues": [
      "allows",
      "demand"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "监管机构需要获取相关记录和信息"
      ],
      "basis_or_condition": [
        "英国《2000年金融服务与市场法》第166条"
      ],
      "focal_handling_or_judgment": "监管机构要求提供客户档案、交易或风险管理流程数据",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002989",
        "quote": "Jurisdictions often grant regulators special provisions to obtain relevant records and information. For example, in the UK, Section 166 of the Financial Services and Markets Act 2000 allows regulators to demand data on customer files, transactions, or risk management processes."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002990"
    ],
    "proposition": "机构必须维护准确记录和结构化治理，以快速响应监管请求并展示有效的金融犯罪防控控制。",
    "source_quotes": [
      "Organizations must maintain accurate records and structured governance to quickly comply with such requests and demonstrate robust AFC controls."
    ],
    "relation_cues": [
      "must",
      "to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "监管请求"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "维护准确记录和结构化治理",
      "outcomes_or_paths": [
        "快速遵从请求",
        "展示有效的金融犯罪防控控制"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002990",
        "quote": "Organizations must maintain accurate records and structured governance to quickly comply with such requests and demonstrate robust AFC controls."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
