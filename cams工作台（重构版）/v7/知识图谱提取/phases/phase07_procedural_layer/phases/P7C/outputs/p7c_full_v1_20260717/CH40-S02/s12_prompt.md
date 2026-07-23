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

section_id: `CH40-S02`

section_title: `Design Your AFC Program and Controls > Case study: Lack of governance at a Canadian bank`

section_text_with_unit_anchors:

```text
[v7u_N002876|2876] In December 2023, the Financial Transactions and Reports Analysis Centre of Canada (FINTRAC) imposed a CA$7.475 million fine on Royal Bank of Canada (RBC) for non-compliance with the Proceeds of Crime (Money Laundering) and Terrorist Financing Act.
ZH: 2023年12月，FINTRAC因加拿大皇家银行违反《犯罪收益（洗钱）和恐怖融资法》对其处以747.5万加元罚款。

[v7u_N002877|2877] The regulator discovered AML/CFT deficiencies during its compliance examination in 2022. Key failures included:
ZH: 监管机构在2022年合规检查中发现反洗钱/反恐怖融资缺陷，主要失败包括以下各项。

[v7u_N002878|2878] RBC failed to file 16 SARs, despite reasonable grounds to suspect that transactions were linked to money laundering activities. In other cases, SARs were filed in a way inconsistent with prescribed regulatory standards.
ZH: RBC未提交16份可疑交易报告，尽管有合理理由怀疑交易与洗钱活动有关。

[v7u_N002879|2879] RBC lacked adequate documented governance for developing, updating, and implementing AML/CTF policies and procedures.
ZH: RBC缺乏足够的有文件记录的治理来制定、更新和实施反洗钱/反恐怖融资政策和程序。

[v7u_N002880|2880] RBC had incomplete procedures for identifying suspicious activity and filing STRs. In addition, the bank kept inconsistent guidance on SAR filings that did not incorporate FINTRAC’s “reasonable grounds” threshold.
ZH: RBC识别可疑活动和提交STR的程序不完整，且关于SAR提交的指引不一致，未纳入FINTRAC的“合理理由”门槛。

[v7u_N002881|2881] This case illustrates how weak oversight can create gaps in key financial crime controls.
ZH: 案例介绍：加拿大银行因治理薄弱导致金融犯罪防控出现漏洞

[v7u_N002882|2882] Due to inadequate governance, RBC failed to develop, update, and implement appropriate policies and procedures.
ZH: RBC因治理不善未能制定、更新和实施适当的政策和程序

[v7u_N002883|2883] The bank did not file SARs as required by law.
ZH: RBC未按法律要求提交可疑交易报告（SAR）

[v7u_N002884|2884] It suffered financial consequences and reputational damage from the enforcement action.
ZH: RBC因执法行动遭受财务损失和声誉损害

[v7u_N002885|2885] AML policies must be dynamic and risk-based.
ZH: 反洗钱政策必须动态且基于风险

[v7u_N002886|2886] Financial institutions must continuously update governance frameworks to align with evolving AML/CFT risks.
ZH: 金融机构必须持续更新治理框架以应对不断变化的洗钱和恐怖融资风险

[v7u_N002887|2887] To ensure strong AML/CFT governance, boards of directors and senior leadership must actively oversee AML compliance.
ZH: 董事会和高级领导层必须积极监督反洗钱合规

[v7u_N002888|2888] AML/CFT policies should be regularly reviewed and updated to reflect new regulatory requirements.
ZH: 反洗钱/反恐怖融资政策应定期审查和更新以反映新的监管要求

[v7u_N002889|2889] Regular, independent audits and testing should be done to ensure governance structures remain effective.
ZH: 应进行定期独立审计和测试以确保治理结构持续有效
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002876",
      "v7u_N002877",
      "v7u_N002878",
      "v7u_N002879",
      "v7u_N002880",
      "v7u_N002881",
      "v7u_N002882",
      "v7u_N002883",
      "v7u_N002884"
    ],
    "proposition": "加拿大皇家银行因治理不善，未能制定适当政策和程序、未按法律要求提交可疑交易报告，导致FINTRAC发现缺陷并处以罚款，遭受财务和声誉损失。",
    "source_quotes": [
      "In December 2023, the Financial Transactions and Reports Analysis Centre of Canada (FINTRAC) imposed a CA$7.475 million fine on Royal Bank of Canada (RBC) for non-compliance with the Proceeds of Crime (Money Laundering) and Terrorist Financing Act.",
      "The regulator discovered AML/CFT deficiencies during its compliance examination in 2022. Key failures included:",
      "RBC failed to file 16 SARs, despite reasonable grounds to suspect that transactions were linked to money laundering activities. In other cases, SARs were filed in a way inconsistent with prescribed regulatory standards.",
      "RBC lacked adequate documented governance for developing, updating, and implementing AML/CTF policies and procedures.",
      "RBC had incomplete procedures for identifying suspicious activity and filing STRs. In addition, the bank kept inconsistent guidance on SAR filings that did not incorporate FINTRAC’s “reasonable grounds” threshold.",
      "This case illustrates how weak oversight can create gaps in key financial crime controls.",
      "Due to inadequate governance, RBC failed to develop, update, and implement appropriate policies and procedures.",
      "The bank did not file SARs as required by law.",
      "It suffered financial consequences and reputational damage from the enforcement action."
    ],
    "relation_cues": [
      "imposed for",
      "discovered",
      "failed",
      "despite",
      "lacked",
      "incomplete",
      "inconsistent",
      "illustrates",
      "due to",
      "suffered"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "监管机构2022年合规检查发现AML/CFT缺陷"
      ],
      "basis_or_condition": [
        "银行缺乏足够文档治理、程序不完整、未纳入合理理由门槛"
      ],
      "focal_handling_or_judgment": "治理不善导致AML/CFT违规和处罚",
      "outcomes_or_paths": [
        "被处以747.5万加元罚款",
        "遭受财务和声誉损失"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002876",
        "quote": "In December 2023, the Financial Transactions and Reports Analysis Centre of Canada (FINTRAC) imposed a CA$7.475 million fine on Royal Bank of Canada (RBC) for non-compliance with the Proceeds of Crime (Money Laundering) and Terrorist Financing Act."
      },
      {
        "unit_id": "v7u_N002877",
        "quote": "The regulator discovered AML/CFT deficiencies during its compliance examination in 2022. Key failures included:"
      },
      {
        "unit_id": "v7u_N002878",
        "quote": "RBC failed to file 16 SARs, despite reasonable grounds to suspect that transactions were linked to money laundering activities. In other cases, SARs were filed in a way inconsistent with prescribed regulatory standards."
      },
      {
        "unit_id": "v7u_N002879",
        "quote": "RBC lacked adequate documented governance for developing, updating, and implementing AML/CTF policies and procedures."
      },
      {
        "unit_id": "v7u_N002880",
        "quote": "RBC had incomplete procedures for identifying suspicious activity and filing STRs. In addition, the bank kept inconsistent guidance on SAR filings that did not incorporate FINTRAC’s “reasonable grounds” threshold."
      },
      {
        "unit_id": "v7u_N002881",
        "quote": "This case illustrates how weak oversight can create gaps in key financial crime controls."
      },
      {
        "unit_id": "v7u_N002882",
        "quote": "Due to inadequate governance, RBC failed to develop, update, and implement appropriate policies and procedures."
      },
      {
        "unit_id": "v7u_N002883",
        "quote": "The bank did not file SARs as required by law."
      },
      {
        "unit_id": "v7u_N002884",
        "quote": "It suffered financial consequences and reputational damage from the enforcement action."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N002885",
      "v7u_N002886",
      "v7u_N002887",
      "v7u_N002888",
      "v7u_N002889"
    ],
    "proposition": "反洗钱政策必须动态且基于风险；金融机构必须持续更新治理框架；董事会和高级领导层必须积极监督；政策应定期审查更新；应进行定期独立审计和测试。",
    "source_quotes": [
      "AML policies must be dynamic and risk-based.",
      "Financial institutions must continuously update governance frameworks to align with evolving AML/CFT risks.",
      "To ensure strong AML/CFT governance, boards of directors and senior leadership must actively oversee AML compliance.",
      "AML/CFT policies should be regularly reviewed and updated to reflect new regulatory requirements.",
      "Regular, independent audits and testing should be done to ensure governance structures remain effective."
    ],
    "relation_cues": [
      "must",
      "should",
      "to ensure",
      "to align",
      "to reflect"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "为了确保AML/CFT合规并应对不断变化的风险"
      ],
      "basis_or_condition": [
        "应对不断变化的AML/CFT风险",
        "反映新的监管要求"
      ],
      "focal_handling_or_judgment": "金融机构必须采取动态风险为本的AML治理措施",
      "outcomes_or_paths": [
        "保持治理结构有效"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002885",
        "quote": "AML policies must be dynamic and risk-based."
      },
      {
        "unit_id": "v7u_N002886",
        "quote": "Financial institutions must continuously update governance frameworks to align with evolving AML/CFT risks."
      },
      {
        "unit_id": "v7u_N002887",
        "quote": "To ensure strong AML/CFT governance, boards of directors and senior leadership must actively oversee AML compliance."
      },
      {
        "unit_id": "v7u_N002888",
        "quote": "AML/CFT policies should be regularly reviewed and updated to reflect new regulatory requirements."
      },
      {
        "unit_id": "v7u_N002889",
        "quote": "Regular, independent audits and testing should be done to ensure governance structures remain effective."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
