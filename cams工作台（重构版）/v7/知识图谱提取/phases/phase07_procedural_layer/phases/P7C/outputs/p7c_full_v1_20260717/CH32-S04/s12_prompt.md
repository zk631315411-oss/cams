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

section_id: `CH32-S04`

section_title: `Cooperation involving the private sector > Private sector collaboration`

section_text_with_unit_anchors:

```text
[v7u_N002329|2329] Money launderers and terrorists actively seek to avoid detection by spreading their activities across multiple financial institutions to avoid triggering an alert in any one institution.
ZH: 洗钱者和恐怖分子通过跨机构分散活动来规避检测

[v7u_N002330|2330] For this reason, it is important that private sector entities collaborate with each other to spot patterns that are only evident when looking across institutions.
ZH: 私营部门实体应合作发现跨机构的模式

[v7u_N002331|2331] Organizations can collaborate via established industry bodies like trade associations, or through bespoke AML entities.
ZH: 组织可通过行业协会或专门的反洗钱实体进行合作

[v7u_N002332|2332] Some groups collaborate to produce guidance.
ZH: 一些合作团体旨在制定指导文件

[v7u_N002333|2333] For example, the Wolfsberg Group develops frameworks and guidance for financial crime risk management. Another example is the Joint Money Laundering Steering Group, an umbrella body through which the UK financial sector produces government-approved guidance.
ZH: 沃尔夫斯堡集团和联合洗钱指导小组是合作制定指南的实例

[v7u_N002334|2334] Other groups collaborate to share industry best practices, such as best practices for suspicious activity reporting. Many of these groups include representatives from public sector bodies or collaborate closely with them. Such groups might also share typologies and information on risks.
ZH: 私营部门合作团体分享最佳实践、类型学和风险信息，并吸纳公共部门代表

[v7u_N002335|2335] Information sharing is an important form of private-to-private sector collaboration.
ZH: 信息共享是私营部门间合作的重要形式

[v7u_N002336|2336] Some jurisdictions have introduced legislation that enables this type of sharing.
ZH: 一些司法管辖区已立法允许此类信息共享

[v7u_N002337|2337] In these jurisdictions, organizations may share data on customers, activity, and transactions.
ZH: 在这些司法管辖区，组织可共享客户、活动和交易数据

[v7u_N002338|2338] This can be highly impactful, resulting in better quality SARs and preventing customers who have been exited by one organization for AML/CFT concerns from opening an account at another.
ZH: 信息共享可提高可疑交易报告质量，防止被退出的客户在其他机构重新开户

[v7u_N002339|2339] Organizations may also come together to develop or share capabilities, such as KYC utilities. These joint platforms allow organizations to pool their resources and expertise and improve the accuracy of their KYC procedures.
ZH: 组织可联合开发了解你的客户公用平台，共享资源并提高了解你的客户准确性

[v7u_N002340|2340] Compliance officers can and should engage in informal collaboration.
ZH: 合规官可以且应当进行非正式合作

[v7u_N002341|2341] Sharing perspectives and experiences with peer organizations can help benchmark controls against those of comparable organizations and identify and adopt best practices.
ZH: 与同业分享观点和经验有助于对标控制措施并采纳最佳实践

[v7u_N002342|2342] Any such discussion should be compliant with local data privacy laws and with the organization’s own requirements regarding the protection of confidential or commercially sensitive information.
ZH: 讨论须遵守当地数据隐私法和机构对保密信息的保护要求
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002329",
      "v7u_N002330",
      "v7u_N002331"
    ],
    "proposition": "洗钱者和恐怖分子跨机构分散活动，因此私营部门实体应合作发现跨机构模式，可通过行业团体或专门反洗钱实体进行合作。",
    "source_quotes": [
      "Money launderers and terrorists actively seek to avoid detection by spreading their activities across multiple financial institutions to avoid triggering an alert in any one institution.",
      "For this reason, it is important that private sector entities collaborate with each other to spot patterns that are only evident when looking across institutions.",
      "Organizations can collaborate via established industry bodies like trade associations, or through bespoke AML entities."
    ],
    "relation_cues": [
      "for this reason",
      "it is important",
      "collaborate",
      "via"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "洗钱者和恐怖分子通过跨机构分散活动来规避检测"
      ],
      "basis_or_condition": [
        "通过行业协会或专门反洗钱实体"
      ],
      "focal_handling_or_judgment": "私营部门实体相互合作",
      "outcomes_or_paths": [
        "发现跨机构模式"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002329",
        "quote": "Money launderers and terrorists actively seek to avoid detection by spreading their activities across multiple financial institutions to avoid triggering an alert in any one institution."
      },
      {
        "unit_id": "v7u_N002330",
        "quote": "For this reason, it is important that private sector entities collaborate with each other to spot patterns that are only evident when looking across institutions."
      },
      {
        "unit_id": "v7u_N002331",
        "quote": "Organizations can collaborate via established industry bodies like trade associations, or through bespoke AML entities."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002332",
      "v7u_N002333",
      "v7u_N002334"
    ],
    "proposition": "一些团体协作制定指导文件，另一些团体协作分享行业最佳实践、类型学和风险信息。",
    "source_quotes": [
      "Some groups collaborate to produce guidance.",
      "For example, the Wolfsberg Group develops frameworks and guidance for financial crime risk management. Another example is the Joint Money Laundering Steering Group, an umbrella body through which the UK financial sector produces government-approved guidance.",
      "Other groups collaborate to share industry best practices, such as best practices for suspicious activity reporting. Many of these groups include representatives from public sector bodies or collaborate closely with them. Such groups might also share typologies and information on risks."
    ],
    "relation_cues": [
      "collaborate",
      "produce",
      "share",
      "might also"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "私营部门团体协作",
      "outcomes_or_paths": [
        "制定指导文件",
        "分享行业最佳实践",
        "分享类型学和风险信息"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002332",
        "quote": "Some groups collaborate to produce guidance."
      },
      {
        "unit_id": "v7u_N002333",
        "quote": "For example, the Wolfsberg Group develops frameworks and guidance for financial crime risk management. Another example is the Joint Money Laundering Steering Group, an umbrella body through which the UK financial sector produces government-approved guidance."
      },
      {
        "unit_id": "v7u_N002334",
        "quote": "Other groups collaborate to share industry best practices, such as best practices for suspicious activity reporting. Many of these groups include representatives from public sector bodies or collaborate closely with them. Such groups might also share typologies and information on risks."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002335",
      "v7u_N002336",
      "v7u_N002337",
      "v7u_N002338"
    ],
    "proposition": "信息共享是私营部门协作的重要形式，在已立法的司法管辖区，组织可共享客户、活动和交易数据，从而提高可疑交易报告质量并防止被退出的客户重新开户。",
    "source_quotes": [
      "Information sharing is an important form of private-to-private sector collaboration.",
      "Some jurisdictions have introduced legislation that enables this type of sharing.",
      "In these jurisdictions, organizations may share data on customers, activity, and transactions.",
      "This can be highly impactful, resulting in better quality SARs and preventing customers who have been exited by one organization for AML/CFT concerns from opening an account at another."
    ],
    "relation_cues": [
      "important form",
      "have introduced legislation",
      "may share",
      "resulting in"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "信息共享是重要协作形式"
      ],
      "basis_or_condition": [
        "一些司法管辖区已立法允许此共享"
      ],
      "focal_handling_or_judgment": "组织共享客户、活动和交易数据",
      "outcomes_or_paths": [
        "提高可疑交易报告质量",
        "防止被AML/CFT退出的客户在其他机构开户"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002335",
        "quote": "Information sharing is an important form of private-to-private sector collaboration."
      },
      {
        "unit_id": "v7u_N002336",
        "quote": "Some jurisdictions have introduced legislation that enables this type of sharing."
      },
      {
        "unit_id": "v7u_N002337",
        "quote": "In these jurisdictions, organizations may share data on customers, activity, and transactions."
      },
      {
        "unit_id": "v7u_N002338",
        "quote": "This can be highly impactful, resulting in better quality SARs and preventing customers who have been exited by one organization for AML/CFT concerns from opening an account at another."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002339"
    ],
    "proposition": "组织可联合开发或共享能力如KYC公用设施，以集中资源提高KYC程序准确性。",
    "source_quotes": [
      "Organizations may also come together to develop or share capabilities, such as KYC utilities. These joint platforms allow organizations to pool their resources and expertise and improve the accuracy of their KYC procedures."
    ],
    "relation_cues": [
      "may also",
      "come together",
      "pool",
      "improve"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "组织联合开发或共享KYC等能力",
      "outcomes_or_paths": [
        "集中资源与专业知识",
        "提高KYC程序准确性"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002339",
        "quote": "Organizations may also come together to develop or share capabilities, such as KYC utilities. These joint platforms allow organizations to pool their resources and expertise and improve the accuracy of their KYC procedures."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002340",
      "v7u_N002341",
      "v7u_N002342"
    ],
    "proposition": "合规官可以且应当进行非正式合作，与同业分享观点和经验以对标控制措施并采纳最佳实践，但须遵守当地数据隐私法和保密要求。",
    "source_quotes": [
      "Compliance officers can and should engage in informal collaboration.",
      "Sharing perspectives and experiences with peer organizations can help benchmark controls against those of comparable organizations and identify and adopt best practices.",
      "Any such discussion should be compliant with local data privacy laws and with the organization’s own requirements regarding the protection of confidential or commercially sensitive information."
    ],
    "relation_cues": [
      "can and should",
      "help benchmark",
      "identify",
      "adopt",
      "should be compliant"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "须遵守当地数据隐私法和机构对保密信息的保护要求"
      ],
      "focal_handling_or_judgment": "合规官进行非正式合作，分享观点和经验",
      "outcomes_or_paths": [
        "对标控制措施",
        "识别和采纳最佳实践"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002340",
        "quote": "Compliance officers can and should engage in informal collaboration."
      },
      {
        "unit_id": "v7u_N002341",
        "quote": "Sharing perspectives and experiences with peer organizations can help benchmark controls against those of comparable organizations and identify and adopt best practices."
      },
      {
        "unit_id": "v7u_N002342",
        "quote": "Any such discussion should be compliant with local data privacy laws and with the organization’s own requirements regarding the protection of confidential or commercially sensitive information."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
