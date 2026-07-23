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

section_id: `CH19-S03`

section_title: `Financial Action Task Force > FATF Recommendations 9-23`

section_text_with_unit_anchors:

```text
[v7u_N001353|1353] FATF Recommendations 9 to 23 seek to ensure the effectiveness of member jurisdictions' measures to detect and prevent illicit financial activities.
ZH: FATF建议9至23旨在确保成员国有效检测和预防非法金融活动

[v7u_N001354|1354] Recommendation 9 advises jurisdictions to ensure that financial institution secrecy laws do not inhibit the implementation of FATF Recommendations.
ZH: FATF建议9要求金融机构保密法不得阻碍FATF建议的实施

[v7u_N001355|1355] Recommendations 10 and 11 require financial institutions to conduct CDD when initiating business relationships, processing occasional transactions above a set threshold, suspecting money laundering or terrorist financing, or questioning the accuracy of previously obtained customer identification data.
ZH: FATF建议10和11规定客户尽职调查的触发情形

[v7u_N001356|1356] Financial institutions should also retain transaction records and CDD information for at least five years to ensure timely compliance with requests from relevant authorities.
ZH: 金融机构应将交易记录和客户尽职调查信息保存至少五年

[v7u_N001357|1357] Recommendations 12 to 16 provide additional measures for specific customers and activities.
ZH: FATF建议12至16针对特定客户和活动规定了额外措施

[v7u_N001358|1358] For instance, financial institutions should identify PEPs, obtain senior management approval to establish a business relationship with a PEP, and verify their sources of wealth and funds.
ZH: 金融机构需识别政治敏感人物并验证其财富和资金来源

[v7u_N001359|1359] Financial institutions should assess respondent institutions’ AML/CFT controls before initiating a correspondent relationship.
ZH: 金融机构在建立代理行关系前应评估代理行的反洗钱/反恐怖融资管控措施

[v7u_N001360|1360] Money or value transfer service providers should be licensed and monitored.
ZH: 货币或价值转移服务提供商须获得许可并接受监管

[v7u_N001361|1361] Financial institutions should assess risks from new technologies and ensure accurate originator and beneficiary data in wire transfers.
ZH: 金融机构需评估新技术风险并确保电汇中发端人和受益人数据准确

[v7u_N001362|1362] Recommendations 17 to 19 advise jurisdictions to allow financial institutions to rely on third-party CDD if it meets certain criteria.
ZH: FATF建议17-19允许金融机构在满足条件时依赖第三方客户尽职调查

[v7u_N001363|1363] Financial institutions should implement AML/CFT programs, facilitate the sharing of information for AML/CFT purposes, and apply enhanced due diligence to business relationships and transactions with persons and institutions from jurisdictions FATF identifies as higher risk.
ZH: 金融机构应实施反洗钱/反恐怖融资计划并对高风险辖区强化尽职调查

[v7u_N001364|1364] Recommendations 20 to 23 discuss the obligation to report suspicious transactions. Financial institutions should report suspicious transactions to the relevant Financial Intelligence Unit (FIU).
ZH: 金融机构有义务向金融情报机构报告可疑交易

[v7u_N001365|1365] Laws should protect financial institutions and their employees from liability and prohibit them from disclosing suspicious transactions.
ZH: 法律应保护金融机构及其员工免于责任并禁止披露可疑交易

[v7u_N001366|1366] Designated nonfinancial businesses and professions (DNFBP) should implement internal controls, report suspicious transactions, and be subject to regulatory and supervisory measures to ensure compliance with AML/CFT requirements.
ZH: 指定非金融行业和职业需实施内部控制、报告可疑交易并接受监管
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001354"
    ],
    "proposition": "建议9要求司法管辖区确保金融机构保密法不阻碍FATF建议的实施。",
    "source_quotes": [
      "Recommendation 9 advises jurisdictions to ensure that financial institution secrecy laws do not inhibit the implementation of FATF Recommendations."
    ],
    "relation_cues": [
      "advises",
      "ensure",
      "not inhibit"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "存在金融机构保密法"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "确保保密法不阻碍FATF建议的实施",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001354",
        "quote": "Recommendation 9 advises jurisdictions to ensure that financial institution secrecy laws do not inhibit the implementation of FATF Recommendations."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001355"
    ],
    "proposition": "建议10和11要求金融机构在特定情形下进行客户尽职调查。",
    "source_quotes": [
      "Recommendations 10 and 11 require financial institutions to conduct CDD when initiating business relationships, processing occasional transactions above a set threshold, suspecting money laundering or terrorist financing, or questioning the accuracy of previously obtained customer identification data."
    ],
    "relation_cues": [
      "require",
      "when"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "建立业务关系",
        "处理超过设定阈值的偶发交易",
        "怀疑洗钱或恐怖融资",
        "怀疑先前获取的客户身份数据准确性"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "进行客户尽职调查",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001355",
        "quote": "Recommendations 10 and 11 require financial institutions to conduct CDD when initiating business relationships, processing occasional transactions above a set threshold, suspecting money laundering or terrorist financing, or questioning the accuracy of previously obtained customer identification data."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001356"
    ],
    "proposition": "金融机构应将交易记录和客户尽职调查信息保存至少五年。",
    "source_quotes": [
      "Financial institutions should also retain transaction records and CDD information for at least five years to ensure timely compliance with requests from relevant authorities."
    ],
    "relation_cues": [
      "should",
      "retain"
    ],
    "candidate_frame": {
      "trigger_or_context": [],
      "basis_or_condition": [
        "为了确保及时响应相关当局的要求"
      ],
      "focal_handling_or_judgment": "保留交易记录和客户尽职调查信息至少五年",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001356",
        "quote": "Financial institutions should also retain transaction records and CDD information for at least five years to ensure timely compliance with requests from relevant authorities."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_004",
    "unit_ids": [
      "v7u_N001358"
    ],
    "proposition": "金融机构应识别政治敏感人物，获得高级管理层批准建立业务关系，并验证其财富和资金来源。",
    "source_quotes": [
      "For instance, financial institutions should identify PEPs, obtain senior management approval to establish a business relationship with a PEP, and verify their sources of wealth and funds."
    ],
    "relation_cues": [
      "should",
      "identify",
      "obtain",
      "verify"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "与政治敏感人物建立业务关系"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "识别PEPs、获得高级管理层批准、验证财富和资金来源",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001358",
        "quote": "For instance, financial institutions should identify PEPs, obtain senior management approval to establish a business relationship with a PEP, and verify their sources of wealth and funds."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_005",
    "unit_ids": [
      "v7u_N001359"
    ],
    "proposition": "金融机构在建立代理行关系前应评估代理行的反洗钱/反恐怖融资管控措施。",
    "source_quotes": [
      "Financial institutions should assess respondent institutions’ AML/CFT controls before initiating a correspondent relationship."
    ],
    "relation_cues": [
      "should",
      "assess",
      "before"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "建立代理行关系"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "评估代理行的反洗钱/反恐怖融资管控措施",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001359",
        "quote": "Financial institutions should assess respondent institutions’ AML/CFT controls before initiating a correspondent relationship."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_006",
    "unit_ids": [
      "v7u_N001360"
    ],
    "proposition": "货币或价值转移服务提供商须获得许可并接受监管。",
    "source_quotes": [
      "Money or value transfer service providers should be licensed and monitored."
    ],
    "relation_cues": [
      "should",
      "licensed",
      "monitored"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "货币或价值转移服务提供商"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "获得许可并接受监管",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001360",
        "quote": "Money or value transfer service providers should be licensed and monitored."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_007",
    "unit_ids": [
      "v7u_N001361"
    ],
    "proposition": "金融机构应评估新技术风险并确保电汇中发端人和受益人数据准确。",
    "source_quotes": [
      "Financial institutions should assess risks from new technologies and ensure accurate originator and beneficiary data in wire transfers."
    ],
    "relation_cues": [
      "should",
      "assess",
      "ensure"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "使用新技术",
        "进行电汇"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "评估新技术风险，确保电汇中发端人和受益人数据准确",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001361",
        "quote": "Financial institutions should assess risks from new technologies and ensure accurate originator and beneficiary data in wire transfers."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_008",
    "unit_ids": [
      "v7u_N001362"
    ],
    "proposition": "建议17-19允许金融机构在满足条件时依赖第三方客户尽职调查。",
    "source_quotes": [
      "Recommendations 17 to 19 advise jurisdictions to allow financial institutions to rely on third-party CDD if it meets certain criteria."
    ],
    "relation_cues": [
      "advise",
      "allow",
      "rely on",
      "if"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "金融机构希望依赖第三方客户尽职调查"
      ],
      "basis_or_condition": [
        "第三方CDD满足特定标准"
      ],
      "focal_handling_or_judgment": "允许依赖第三方客户尽职调查",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001362",
        "quote": "Recommendations 17 to 19 advise jurisdictions to allow financial institutions to rely on third-party CDD if it meets certain criteria."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_009",
    "unit_ids": [
      "v7u_N001363"
    ],
    "proposition": "金融机构应实施反洗钱/反恐怖融资计划，促进信息共享，并对高风险辖区强化尽职调查。",
    "source_quotes": [
      "Financial institutions should implement AML/CFT programs, facilitate the sharing of information for AML/CFT purposes, and apply enhanced due diligence to business relationships and transactions with persons and institutions from jurisdictions FATF identifies as higher risk."
    ],
    "relation_cues": [
      "should",
      "implement",
      "facilitate",
      "apply"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "与FATF识别的高风险辖区的人或机构开展业务关系或交易"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "实施反洗钱/反恐怖融资计划，促进信息共享，应用强化尽职调查",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001363",
        "quote": "Financial institutions should implement AML/CFT programs, facilitate the sharing of information for AML/CFT purposes, and apply enhanced due diligence to business relationships and transactions with persons and institutions from jurisdictions FATF identifies as higher risk."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_010",
    "unit_ids": [
      "v7u_N001364"
    ],
    "proposition": "金融机构应向相关金融情报机构报告可疑交易。",
    "source_quotes": [
      "Financial institutions should report suspicious transactions to the relevant Financial Intelligence Unit (FIU)."
    ],
    "relation_cues": [
      "should",
      "report"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "发现可疑交易"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "向金融情报机构报告可疑交易",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001364",
        "quote": "Financial institutions should report suspicious transactions to the relevant Financial Intelligence Unit (FIU)."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_011",
    "unit_ids": [
      "v7u_N001365"
    ],
    "proposition": "法律应保护金融机构及其员工免于责任，并禁止披露可疑交易。",
    "source_quotes": [
      "Laws should protect financial institutions and their employees from liability and prohibit them from disclosing suspicious transactions."
    ],
    "relation_cues": [
      "should",
      "protect",
      "prohibit"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "金融机构及其员工报告可疑交易"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "保护免于责任，禁止披露可疑交易",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001365",
        "quote": "Laws should protect financial institutions and their employees from liability and prohibit them from disclosing suspicious transactions."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_012",
    "unit_ids": [
      "v7u_N001366"
    ],
    "proposition": "指定非金融行业和职业应实施内部控制、报告可疑交易并接受监管以确保合规。",
    "source_quotes": [
      "Designated nonfinancial businesses and professions (DNFBP) should implement internal controls, report suspicious transactions, and be subject to regulatory and supervisory measures to ensure compliance with AML/CFT requirements."
    ],
    "relation_cues": [
      "should",
      "implement",
      "report",
      "be subject to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "指定非金融行业和职业"
      ],
      "basis_or_condition": [],
      "focal_handling_or_judgment": "实施内部控制，报告可疑交易，接受监管措施以遵守反洗钱/反恐怖融资要求",
      "outcomes_or_paths": []
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001366",
        "quote": "Designated nonfinancial businesses and professions (DNFBP) should implement internal controls, report suspicious transactions, and be subject to regulatory and supervisory measures to ensure compliance with AML/CFT requirements."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
