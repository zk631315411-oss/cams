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

section_id: `CH26-S04`

section_title: `Other laws and regulations that impact organizations > The GDPR and the balance between privacy and transparency`

section_text_with_unit_anchors:

```text
[v7u_N002057|2057] The GDPR applies to all data processing activities. These include activities where an organization processes personal data to comply with other regulations it is subject to, such as data gathering for AML purposes.
ZH: 《通用数据保护条例》适用于所有数据处理活动，包括为反洗钱合规目的收集数据

[v7u_N002058|2058] AML obligations require organizations to obtain and process the personal data of relevant data subjects when performing KYC tasks. These tasks can include gathering ultimate beneficial ownership information and customer identification information such as the full name and date of birth of individual directors.
ZH: 反洗钱义务要求组织在执行了解你的客户任务时获取和处理数据主体的个人数据

[v7u_N002059|2059] The GDPR applies to all organizations that use personal data and are established in the EU or that fall within the extraterritorial scope of the law.
ZH: 《通用数据保护条例》适用于在欧盟设立或属于域外适用范围的所有使用个人数据的组织

[v7u_N002060|2060] Therefore, organizations must adhere to AML obligations and the GDPR.
ZH: 组织必须同时遵守反洗钱义务和《通用数据保护条例》

[v7u_N002061|2061] The GDPR obliges organizations to provide data subjects with a variety of rights regarding their personal data. These rights can include a right of access, a right to deletion, and the right to be informed, also referred to as transparency. The GDPR requires organizations to inform data subjects about why and how the organization will use their personal data.
ZH: 《通用数据保护条例》要求组织赋予数据主体访问、删除、知情等权利，并履行透明度义务。

[v7u_N002062|2062] Articles 75 and 76 of Regulation (EU) 2024/1624 of the European Parliament and of the Council also reference these requirements and state the permissible instances where organizations or other obliged entities may share or process relevant personal information for AML compliance purposes.
ZH: 欧盟第2024/1624号条例第75和76条引用《通用数据保护条例》要求，允许为反洗钱合规目的共享或处理个人信息。

[v7u_N002063|2063] For organizations to lawfully obtain and process personal data, they need at least one lawful reason.
ZH: 组织合法获取和处理个人数据需要至少一项合法理由。

[v7u_N002064|2064] The GDPR provides a list of lawful grounds available for processing standard forms of personal data, such as ID and proof of address information.
ZH: 《通用数据保护条例》列出了处理标准个人数据（如身份证明和地址证明）的合法依据清单。

[v7u_N002065|2065] Additionally, the GDPR states exemptions for the processing of special and sensitive forms of personal data.
ZH: 《通用数据保护条例》规定了特殊和敏感个人数据处理的豁免情形。

[v7u_N002066|2066] This data can include information on race, ethnicity, or political beliefs, as determined from an organization’s KYC information. This data can also include criminal convictions and offenses.
ZH: 特殊类别数据包括从了解你的客户信息中获取的种族、民族或政治信仰，以及刑事定罪和犯罪记录。

[v7u_N002067|2067] The AML regulation states that organizations can use these forms of personal data under the condition that they apply appropriate transparency measures.
ZH: 反洗钱法规规定，组织在采取适当透明度措施的条件下可使用这些个人数据。

[v7u_N002068|2068] Note that data subject rights are not absolute. The offense of tipping off under AML law will impact the extent to which an organization can share certain details of its processing activities with a relevant data subject.
ZH: 数据主体权利并非绝对；反洗钱法中的“泄密”罪限制了组织向数据主体披露处理活动细节的程度。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002057",
      "v7u_N002059"
    ],
    "proposition": "GDPR适用于所有数据处理活动，包括为反洗钱合规目的收集数据，并适用于在欧盟设立或属于域外适用范围的所有使用个人数据的组织。",
    "source_quotes": [
      "The GDPR applies to all data processing activities. These include activities where an organization processes personal data to comply with other regulations it is subject to, such as data gathering for AML purposes.",
      "The GDPR applies to all organizations that use personal data and are established in the EU or that fall within the extraterritorial scope of the law."
    ],
    "relation_cues": [
      "applies to",
      "include"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "数据处理活动（包括反洗钱数据收集）",
        "组织在欧盟设立或属于域外适用范围"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "GDPR适用",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002057",
        "quote": "The GDPR applies to all data processing activities. These include activities where an organization processes personal data to comply with other regulations it is subject to, such as data gathering for AML purposes."
      },
      {
        "unit_id": "v7u_N002059",
        "quote": "The GDPR applies to all organizations that use personal data and are established in the EU or that fall within the extraterritorial scope of the law."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002060"
    ],
    "proposition": "组织必须同时遵守反洗钱义务和《通用数据保护条例》。",
    "source_quotes": [
      "Therefore, organizations must adhere to AML obligations and the GDPR."
    ],
    "relation_cues": [
      "therefore",
      "must"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织同时受AML义务和GDPR约束"
      ],
      "basis_or_condition": [
        "AML义务和GDPR规定"
      ],
      "focal_handling_or_judgment": "必须遵守两者",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002060",
        "quote": "Therefore, organizations must adhere to AML obligations and the GDPR."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002061"
    ],
    "proposition": "GDPR要求组织向数据主体提供访问、删除、知情等权利，并履行透明度义务。",
    "source_quotes": [
      "The GDPR obliges organizations to provide data subjects with a variety of rights regarding their personal data. These rights can include a right of access, a right to deletion, and the right to be informed, also referred to as transparency. The GDPR requires organizations to inform data subjects about why and how the organization will use their personal data."
    ],
    "relation_cues": [
      "obliges",
      "requires"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织处理个人数据"
      ],
      "basis_or_condition": [
        "GDPR规定"
      ],
      "focal_handling_or_judgment": "提供数据主体权利并履行透明度义务",
      "outcomes_or_paths": [
        "数据主体可行使访问、删除、知情等权利"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002061",
        "quote": "The GDPR obliges organizations to provide data subjects with a variety of rights regarding their personal data. These rights can include a right of access, a right to deletion, and the right to be informed, also referred to as transparency. The GDPR requires organizations to inform data subjects about why and how the organization will use their personal data."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002062"
    ],
    "proposition": "欧盟第2024/1624号条例第75和76条允许组织为反洗钱合规目的共享或处理相关个人信息。",
    "source_quotes": [
      "Articles 75 and 76 of Regulation (EU) 2024/1624 of the European Parliament and of the Council also reference these requirements and state the permissible instances where organizations or other obliged entities may share or process relevant personal information for AML compliance purposes."
    ],
    "relation_cues": [
      "may",
      "for AML compliance purposes"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织有反洗钱合规需求"
      ],
      "basis_or_condition": [
        "欧盟第2024/1624号条例第75和76条"
      ],
      "focal_handling_or_judgment": "允许共享或处理相关个人信息",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002062",
        "quote": "Articles 75 and 76 of Regulation (EU) 2024/1624 of the European Parliament and of the Council also reference these requirements and state the permissible instances where organizations or other obliged entities may share or process relevant personal information for AML compliance purposes."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002063",
      "v7u_N002064",
      "v7u_N002065"
    ],
    "proposition": "组织合法获取和处理个人数据需要至少一项合法理由；GDPR列出了处理标准个人数据的合法依据，并对特殊和敏感个人数据的处理规定了豁免情形。",
    "source_quotes": [
      "For organizations to lawfully obtain and process personal data, they need at least one lawful reason.",
      "The GDPR provides a list of lawful grounds available for processing standard forms of personal data, such as ID and proof of address information.",
      "Additionally, the GDPR states exemptions for the processing of special and sensitive forms of personal data."
    ],
    "relation_cues": [
      "need",
      "provides",
      "states exemptions"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织需要合法获取和处理个人数据"
      ],
      "basis_or_condition": [
        "GDPR规定"
      ],
      "focal_handling_or_judgment": "确定合法理由或豁免情形",
      "outcomes_or_paths": [
        "使用GDPR列出的合法依据",
        "适用特殊数据豁免"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002063",
        "quote": "For organizations to lawfully obtain and process personal data, they need at least one lawful reason."
      },
      {
        "unit_id": "v7u_N002064",
        "quote": "The GDPR provides a list of lawful grounds available for processing standard forms of personal data, such as ID and proof of address information."
      },
      {
        "unit_id": "v7u_N002065",
        "quote": "Additionally, the GDPR states exemptions for the processing of special and sensitive forms of personal data."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N002067"
    ],
    "proposition": "反洗钱法规允许组织在采取适当透明度措施的条件下使用特殊类别个人数据（如种族、政治信仰、刑事定罪等）。",
    "source_quotes": [
      "The AML regulation states that organizations can use these forms of personal data under the condition that they apply appropriate transparency measures."
    ],
    "relation_cues": [
      "can",
      "under the condition that"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织需要处理特殊类别个人数据"
      ],
      "basis_or_condition": [
        "反洗钱法规",
        "采取适当透明度措施"
      ],
      "focal_handling_or_judgment": "允许使用特殊类别个人数据",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002067",
        "quote": "The AML regulation states that organizations can use these forms of personal data under the condition that they apply appropriate transparency measures."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N002068"
    ],
    "proposition": "数据主体权利并非绝对；反洗钱法中的“泄密”罪将限制组织向数据主体披露处理活动细节的程度。",
    "source_quotes": [
      "Note that data subject rights are not absolute. The offense of tipping off under AML law will impact the extent to which an organization can share certain details of its processing activities with a relevant data subject."
    ],
    "relation_cues": [
      "not absolute",
      "will impact"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "数据主体主张权利"
      ],
      "basis_or_condition": [
        "反洗钱法中的“泄密”罪"
      ],
      "focal_handling_or_judgment": "数据主体权利受限",
      "outcomes_or_paths": [
        "组织不能完全共享处理活动细节"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002068",
        "quote": "Note that data subject rights are not absolute. The offense of tipping off under AML law will impact the extent to which an organization can share certain details of its processing activities with a relevant data subject."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
