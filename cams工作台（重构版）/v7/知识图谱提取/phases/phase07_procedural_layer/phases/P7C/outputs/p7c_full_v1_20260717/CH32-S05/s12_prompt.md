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

section_id: `CH32-S05`

section_title: `Cooperation involving the private sector > Private sector information sharing`

section_text_with_unit_anchors:

```text
[v7u_N002343|2343] Private sector information sharing provides organizations with information they would not otherwise have, creating opportunities to identify and mitigate risk.
ZH: 私营部门信息共享可提供机构原本无法获取的信息，有助于识别和缓释风险

[v7u_N002344|2344] For example, if Bank A suspects money laundering from a customer, it might offboard them.
ZH: 例如，若A银行怀疑某客户洗钱，可能终止其账户

[v7u_N002345|2345] However, that customer can then easily open an account with Bank B and continue laundering money. Information sharing prevents this and other typologies, leading to better prevention and detection of money laundering and terrorist financing.
ZH: 信息共享可防止客户转向其他机构继续洗钱，提升洗钱和恐怖融资的预防与检测能力

[v7u_N002346|2346] There are various methods of sharing information in the private sector, often developed via public-private partnerships.
ZH: 私营部门有多种信息共享方式，通常通过公私伙伴关系发展而来

[v7u_N002347|2347] USA PATRIOT Act Section 314b is one of the oldest examples.
ZH: 美国《爱国者法案》第314b条是最早的私营部门信息共享示例之一

[v7u_N002348|2348] 314b allows financial institutions to share customer or transactional information with each other to assist with AML/CFT compliance.
ZH: 第314b条允许金融机构相互共享客户或交易信息以协助反洗钱/反恐怖融资合规

[v7u_N002349|2349] It provides participating organizations with a safe harbor from legal liability.
ZH: 第314b条为参与机构提供安全港，免除法律责任

[v7u_N002350|2350] US organizations widely use 314b to identify money laundering and terrorist financing and help decide whether to maintain an account.
ZH: 美国机构广泛使用第314b条识别洗钱和恐怖融资，并协助决定是否保留账户

[v7u_N002351|2351] In the UK, the Economic Crime and Corporate Transparency Act 2023 provides the legal means for two regulated organizations to share information with each other. Like Section 314b in the US, the act exempts such disclosures from civil liability and confidentiality obligations.
ZH: 英国《2023年经济犯罪与公司透明度法案》允许两家受监管机构共享信息，并豁免民事责任和保密义务

[v7u_N002352|2352] Other examples of private-to-private sector sharing exist globally. For example, in Singapore, COSMIC is a digitally secure platform that allows financial institutions to share information. When a customer exhibits “red flags” indicating potential financial crime concerns, financial institutions can share information if certain thresholds are met.
ZH: 新加坡COSMIC平台允许金融机构在客户出现红旗信号信号时共享信息

[v7u_N002353|2353] In the EU, Article 75 of Regulation (EU) 2024/1624 allows organizations to take part in cross-border information sharing partnerships, if their national supervisor approves it. Organizations may share information about customer identity, business relationships, transactions, and customer risk factors.
ZH: 欧盟(EU)2024/1624号法规第75条允许经国家监管机构批准的跨境信息共享伙伴关系

[v7u_N002354|2354] Organizations looking to join private-to-private sector information sharing arrangements should carefully consider their obligations under local data protection legislation and customer confidentiality requirements within their organization.
ZH: 加入私营部门信息共享安排前须考虑当地数据保护法和客户保密义务

[v7u_N002355|2355] National supervisor approval under Article 75 requires the partnership to carry out a data protection impact assessment before processing personal information.
ZH: 第75条要求伙伴关系在处理个人信息前进行数据保护影响评估

[v7u_N002356|2356] If proceeding, organizations should assign appropriate resources and develop policies and procedures to govern the activity.
ZH: 机构应分配适当资源并制定政策和程序来管理信息共享活动

[v7u_N002357|2357] The potential benefits are significant. Appropriate private-to-private information sharing can considerably enhance an AML/CFT program.
ZH: 适当的私营部门信息共享可显著增强反洗钱/反恐怖融资计划
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002348",
      "v7u_N002349"
    ],
    "proposition": "美国《爱国者法案》第314b条允许金融机构共享客户或交易信息以协助反洗钱/反恐融资合规，并为参与机构提供安全港免除法律责任。",
    "source_quotes": [
      "314b allows financial institutions to share customer or transactional information with each other to assist with AML/CFT compliance.",
      "It provides participating organizations with a safe harbor from legal liability."
    ],
    "relation_cues": [
      "allows",
      "provides",
      "safe harbor"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "金融机构希望共享信息以协助合规"
      ],
      "basis_or_condition": [
        "《爱国者法案》第314b条"
      ],
      "focal_handling_or_judgment": "法律允许共享信息并提供安全港",
      "outcomes_or_paths": [
        "协助反洗钱/反恐融资合规",
        "免除法律责任"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002348",
        "quote": "314b allows financial institutions to share customer or transactional information with each other to assist with AML/CFT compliance."
      },
      {
        "unit_id": "v7u_N002349",
        "quote": "It provides participating organizations with a safe harbor from legal liability."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002351"
    ],
    "proposition": "英国《2023年经济犯罪与公司透明度法案》允许两家受监管机构共享信息，并豁免民事责任和保密义务。",
    "source_quotes": [
      "In the UK, the Economic Crime and Corporate Transparency Act 2023 provides the legal means for two regulated organizations to share information with each other. Like Section 314b in the US, the act exempts such disclosures from civil liability and confidentiality obligations."
    ],
    "relation_cues": [
      "provides",
      "exempts"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "受监管机构希望共享信息"
      ],
      "basis_or_condition": [
        "英国《2023年经济犯罪与公司透明度法案》"
      ],
      "focal_handling_or_judgment": "法律允许信息共享并提供豁免",
      "outcomes_or_paths": [
        "豁免民事责任和保密义务"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002351",
        "quote": "In the UK, the Economic Crime and Corporate Transparency Act 2023 provides the legal means for two regulated organizations to share information with each other. Like Section 314b in the US, the act exempts such disclosures from civil liability and confidentiality obligations."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002352"
    ],
    "proposition": "新加坡COSMIC平台允许金融机构在客户出现红旗标志且达到特定阈值时共享信息。",
    "source_quotes": [
      "Other examples of private-to-private sector sharing exist globally. For example, in Singapore, COSMIC is a digitally secure platform that allows financial institutions to share information. When a customer exhibits “red flags” indicating potential financial crime concerns, financial institutions can share information if certain thresholds are met."
    ],
    "relation_cues": [
      "allows",
      "When",
      "if",
      "thresholds"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "客户出现红旗标志 indicating potential financial crime concerns"
      ],
      "basis_or_condition": [
        "达到特定阈值",
        "COSMIC平台"
      ],
      "focal_handling_or_judgment": "金融机构可以共享信息",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002352",
        "quote": "Other examples of private-to-private sector sharing exist globally. For example, in Singapore, COSMIC is a digitally secure platform that allows financial institutions to share information. When a customer exhibits “red flags” indicating potential financial crime concerns, financial institutions can share information if certain thresholds are met."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002353",
      "v7u_N002355"
    ],
    "proposition": "欧盟(EU)2024/1624号法规第75条允许经国家监管机构批准的跨境信息共享伙伴关系，并要求在处理个人信息前进行数据保护影响评估。",
    "source_quotes": [
      "In the EU, Article 75 of Regulation (EU) 2024/1624 allows organizations to take part in cross-border information sharing partnerships, if their national supervisor approves it. Organizations may share information about customer identity, business relationships, transactions, and customer risk factors.",
      "National supervisor approval under Article 75 requires the partnership to carry out a data protection impact assessment before processing personal information."
    ],
    "relation_cues": [
      "allows",
      "if",
      "requires"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织希望参与跨境信息共享伙伴关系"
      ],
      "basis_or_condition": [
        "国家监管机构批准",
        "Article 75规定"
      ],
      "focal_handling_or_judgment": "允许参与伙伴关系并共享信息；要求进行数据保护影响评估",
      "outcomes_or_paths": [
        "共享客户身份、业务关系、交易和风险因素信息",
        "进行数据保护影响评估"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002353",
        "quote": "In the EU, Article 75 of Regulation (EU) 2024/1624 allows organizations to take part in cross-border information sharing partnerships, if their national supervisor approves it. Organizations may share information about customer identity, business relationships, transactions, and customer risk factors."
      },
      {
        "unit_id": "v7u_N002355",
        "quote": "National supervisor approval under Article 75 requires the partnership to carry out a data protection impact assessment before processing personal information."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002354"
    ],
    "proposition": "组织在加入私营部门信息共享安排前应仔细考虑当地数据保护法和客户保密义务。",
    "source_quotes": [
      "Organizations looking to join private-to-private sector information sharing arrangements should carefully consider their obligations under local data protection legislation and customer confidentiality requirements within their organization."
    ],
    "relation_cues": [
      "looking to join",
      "should carefully consider"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织考虑加入私营部门信息共享安排"
      ],
      "basis_or_condition": [
        "当地数据保护法和客户保密义务"
      ],
      "focal_handling_or_judgment": "应仔细考虑相关义务",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002354",
        "quote": "Organizations looking to join private-to-private sector information sharing arrangements should carefully consider their obligations under local data protection legislation and customer confidentiality requirements within their organization."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N002356"
    ],
    "proposition": "如果继续，组织应分配适当资源并制定政策和程序来管理信息共享活动。",
    "source_quotes": [
      "If proceeding, organizations should assign appropriate resources and develop policies and procedures to govern the activity."
    ],
    "relation_cues": [
      "If",
      "should"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "决定继续信息共享安排"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "分配资源并制定政策和程序",
      "outcomes_or_paths": [
        "管理信息共享活动"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002356",
        "quote": "If proceeding, organizations should assign appropriate resources and develop policies and procedures to govern the activity."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N002344"
    ],
    "proposition": "如果银行怀疑客户洗钱，可能终止其账户。",
    "source_quotes": [
      "For example, if Bank A suspects money laundering from a customer, it might offboard them."
    ],
    "relation_cues": [
      "if",
      "might"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "银行怀疑客户洗钱"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "可能终止客户账户",
      "outcomes_or_paths": [
        "终止账户"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002344",
        "quote": "For example, if Bank A suspects money laundering from a customer, it might offboard them."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
