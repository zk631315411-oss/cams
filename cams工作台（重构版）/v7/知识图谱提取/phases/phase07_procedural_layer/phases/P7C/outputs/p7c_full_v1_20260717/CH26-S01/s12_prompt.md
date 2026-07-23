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

section_id: `CH26-S01`

section_title: `Other laws and regulations that impact organizations > Data security and privacy`

section_text_with_unit_anchors:

```text
[v7u_N002011|2011] Financial institutions have a high duty to care for—and often a legal obligation to ensure the security and privacy of—customer data.
ZH: 金融机构对客户数据安全与隐私负有高度注意义务和法律责任。

[v7u_N002012|2012] Your customer data must be stored securely and should only be shared with others who need to know and have the requisite permission and authority to view it.
ZH: 客户数据必须安全存储，仅限有需要且获授权的人员查看。

[v7u_N002013|2013] In many jurisdictions, it is prohibited by law for data collected for one purpose to be used for another purpose, such as marketing.
ZH: 许多司法管辖区禁止将收集的数据用于其他目的（如营销）。

[v7u_N002014|2014] Once it has served its purpose, data must be securely destroyed.
ZH: 数据在完成目的后必须安全销毁。

[v7u_N002015|2015] Many jurisdictions have rules and regulations about how long data should be retained.
ZH: 许多司法管辖区对数据保留期限有规定。

[v7u_N002016|2016] Your organization will have a policy on data categorization, how long data should be stored, and when data should be destroyed.
ZH: 组织应有数据分类、存储期限和销毁政策。

[v7u_N002017|2017] Many jurisdictions have specific national privacy or data security laws, including laws and regulations that apply to financial institutions.
ZH: 许多司法管辖区有专门的国家隐私或数据安全法律，适用于金融机构。

[v7u_N002018|2018] One of the strictest is the EU GDPR for how organizations protect EU citizens' personal data and privacy.
ZH: 欧盟《通用数据保护条例》是保护个人数据和隐私最严格的法律之一。

[v7u_N002019|2019] These laws place challenging requirements on financial institutions that collect data.
ZH: 这些法律对收集数据的金融机构提出了严格要求。

[v7u_N002020|2020] Data privacy laws may place restrictions on the transfer of personal data outside the jurisdiction unless certain conditions are met. These conditions are intended to ensure that protections outside the jurisdiction are equivalent to those in the home jurisdiction.
ZH: 数据隐私法可能限制将个人数据转移至境外，除非满足同等保护条件。

[v7u_N002021|2021] As a result, financial institutions must ensure that they have met the conditions to allow for the transfer of data without violating the laws affected if a data breach occurs.
ZH: 金融机构在数据泄露时必须满足数据传输条件，不违反相关法律。

[v7u_N002022|2022] The data that is collected is comprehensive and often purposeful.
ZH: 收集的数据全面且通常有特定目的。

[v7u_N002023|2023] Care must be taken to ensure physical data is properly protected. It should not be left on an employee’s desk overnight.
ZH: 必须妥善保护物理数据，不得留在员工桌上过夜。

[v7u_N002024|2024] When stored electronically, data must be entered into your organization’s approved databases in accordance with policy.
ZH: 电子数据必须按照政策录入机构批准的数据库。

[v7u_N002025|2025] Some organizations prohibit the use of desktop folders.
ZH: 部分机构禁止使用桌面文件夹存储数据。

[v7u_N002026|2026] Most organizations also prohibit the use of USB sticks for storing data, as these are easily lost.
ZH: 多数机构禁止使用U盘存储数据，因其易丢失。

[v7u_N002027|2027] Data should not be retained indefinitely and must be destroyed in accordance with your organization’s destruction policy.
ZH: 数据不得无限期保留，必须按销毁政策销毁。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002012"
    ],
    "proposition": "客户数据必须安全存储，且仅限有需要并获授权的人员查看。",
    "source_quotes": [
      "Your customer data must be stored securely and should only be shared with others who need to know and have the requisite permission and authority to view it."
    ],
    "relation_cues": [
      "must",
      "should only"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "客户数据"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "安全存储并限制共享权限",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002012",
        "quote": "Your customer data must be stored securely and should only be shared with others who need to know and have the requisite permission and authority to view it."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002013"
    ],
    "proposition": "禁止将收集的数据用于其他目的（如营销）。",
    "source_quotes": [
      "In many jurisdictions, it is prohibited by law for data collected for one purpose to be used for another purpose, such as marketing."
    ],
    "relation_cues": [
      "prohibited",
      "by law"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "数据收集时有特定目的"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "禁止将数据用于其他目的",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002013",
        "quote": "In many jurisdictions, it is prohibited by law for data collected for one purpose to be used for another purpose, such as marketing."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N002014",
      "v7u_N002027"
    ],
    "proposition": "数据完成用途后必须安全销毁；数据不得无限期保留，且须按组织销毁政策销毁。",
    "source_quotes": [
      "Once it has served its purpose, data must be securely destroyed.",
      "Data should not be retained indefinitely and must be destroyed in accordance with your organization’s destruction policy."
    ],
    "relation_cues": [
      "must",
      "should not",
      "must"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "数据完成用途",
        "数据需要根据组织销毁政策销毁"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "安全销毁数据",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002014",
        "quote": "Once it has served its purpose, data must be securely destroyed."
      },
      {
        "unit_id": "v7u_N002027",
        "quote": "Data should not be retained indefinitely and must be destroyed in accordance with your organization’s destruction policy."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N002016"
    ],
    "proposition": "组织应制定数据分类、存储期限和销毁政策。",
    "source_quotes": [
      "Your organization will have a policy on data categorization, how long data should be stored, and when data should be destroyed."
    ],
    "relation_cues": [
      "will have"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "组织"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "制定数据分类、存储期限和销毁政策",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002016",
        "quote": "Your organization will have a policy on data categorization, how long data should be stored, and when data should be destroyed."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N002017"
    ],
    "proposition": "许多司法管辖区有专门的国家隐私或数据安全法律，适用于金融机构。",
    "source_quotes": [
      "Many jurisdictions have specific national privacy or data security laws, including laws and regulations that apply to financial institutions."
    ],
    "relation_cues": [
      "apply to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "金融机构"
      ],
      "basis_or_condition": [
        "国家隐私或数据安全法律"
      ],
      "focal_handling_or_judgment": "法律适用于金融机构",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002017",
        "quote": "Many jurisdictions have specific national privacy or data security laws, including laws and regulations that apply to financial institutions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N002020"
    ],
    "proposition": "数据隐私法可能限制将个人数据跨境转移，除非满足同等保护条件。",
    "source_quotes": [
      "Data privacy laws may place restrictions on the transfer of personal data outside the jurisdiction unless certain conditions are met."
    ],
    "relation_cues": [
      "may",
      "unless"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "个人数据跨境转移"
      ],
      "basis_or_condition": [
        "除非满足同等保护条件"
      ],
      "focal_handling_or_judgment": "限制数据跨境转移",
      "outcomes_or_paths": [
        "可能被限制"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002020",
        "quote": "Data privacy laws may place restrictions on the transfer of personal data outside the jurisdiction unless certain conditions are met."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N002021"
    ],
    "proposition": "金融机构在数据泄露时必须确保满足数据传输条件，不违反相关法律。",
    "source_quotes": [
      "As a result, financial institutions must ensure that they have met the conditions to allow for the transfer of data without violating the laws affected if a data breach occurs."
    ],
    "relation_cues": [
      "must",
      "if"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "数据泄露"
      ],
      "basis_or_condition": [
        "必须满足数据传输条件"
      ],
      "focal_handling_or_judgment": "确保数据传输合法",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002021",
        "quote": "As a result, financial institutions must ensure that they have met the conditions to allow for the transfer of data without violating the laws affected if a data breach occurs."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_008",
    "unit_ids": [
      "v7u_N002023"
    ],
    "proposition": "必须妥善保护物理数据，不得留在员工桌上过夜。",
    "source_quotes": [
      "Care must be taken to ensure physical data is properly protected. It should not be left on an employee’s desk overnight."
    ],
    "relation_cues": [
      "must",
      "should not"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "物理数据"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "妥善保护物理数据，禁止留在桌上过夜",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002023",
        "quote": "Care must be taken to ensure physical data is properly protected. It should not be left on an employee’s desk overnight."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_009",
    "unit_ids": [
      "v7u_N002024"
    ],
    "proposition": "电子数据必须按照组织政策录入批准的数据库。",
    "source_quotes": [
      "When stored electronically, data must be entered into your organization’s approved databases in accordance with policy."
    ],
    "relation_cues": [
      "must",
      "in accordance with"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "电子数据"
      ],
      "basis_or_condition": [
        "按照组织政策"
      ],
      "focal_handling_or_judgment": "录入批准的数据库",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002024",
        "quote": "When stored electronically, data must be entered into your organization’s approved databases in accordance with policy."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_010",
    "unit_ids": [
      "v7u_N002025"
    ],
    "proposition": "部分组织禁止使用桌面文件夹存储数据。",
    "source_quotes": [
      "Some organizations prohibit the use of desktop folders."
    ],
    "relation_cues": [
      "prohibit"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "数据存储"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "禁止使用桌面文件夹",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002025",
        "quote": "Some organizations prohibit the use of desktop folders."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_011",
    "unit_ids": [
      "v7u_N002026"
    ],
    "proposition": "多数组织禁止使用U盘存储数据，因其易丢失。",
    "source_quotes": [
      "Most organizations also prohibit the use of USB sticks for storing data, as these are easily lost."
    ],
    "relation_cues": [
      "prohibit",
      "as"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "数据存储"
      ],
      "basis_or_condition": [
        "因其易丢失"
      ],
      "focal_handling_or_judgment": "禁止使用U盘",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002026",
        "quote": "Most organizations also prohibit the use of USB sticks for storing data, as these are easily lost."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
