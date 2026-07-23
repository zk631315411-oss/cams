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

section_id: `CH30-S02`

section_title: `Using reports, guidance notes, and policy papers in your AML/CFT controls > Case example: Terrorist financing red flags`

section_text_with_unit_anchors:

```text
[v7u_N002165|2165] A regulator issues a report describing new information on how a major terrorist group finances itself. The report contains a list of red flags to look for.
ZH: 监管机构发布关于恐怖融资新信息的报告，并列出需关注的红旗信号信号。

[v7u_N002166|2166] The money laundering reporting officer (MLRO) considers how the bank can incorporate the list of red flags into its AML/CFT controls.
ZH: 反洗钱报告官（洗钱RO）考虑将红旗信号信号纳入机构的 反洗钱/反恐怖融资 控制措施。

[v7u_N002167|2167] The bank’s home regulator issued the document, and while the bank is not legally required to implement the guidance, the regulator expects that the bank will consider it.
ZH: 尽管无法律强制要求，监管机构期望银行考虑其发布的指导文件。

[v7u_N002168|2168] The MLRO conducts a review of the bank’s existing controls and processes to determine which areas are impacted. She then analyzes whether appropriate controls are in place and whether any gaps need to be addressed.
ZH: MLRO 审查现有控制措施和流程，分析差距并确定受影响领域。

[v7u_N002169|2169] One red flag identifies the use of import/export companies with a connection to certain jurisdictions.
ZH: 红旗信号信号：与特定司法管辖区有关联的进出口公司。

[v7u_N002170|2170] The bank has numerous import/export companies as clients. It has EDD procedures in place to provide extra scrutiny of such companies.
ZH: 银行拥有众多进出口公司客户，并已建立强化尽职调查（EDD）程序。

[v7u_N002171|2171] The MLRO reviews the bank’s procedures to assess alignment with the red flag.
ZH: MLRO 审查银行现有程序，评估其与红旗信号信号的一致性。

[v7u_N002172|2172] She finds that the bank asks all its import/export companies for extra information at onboarding and subjects them to an annual review.
ZH: 银行要求所有进出口公司在开户时提供额外信息并接受年度审查。

[v7u_N002173|2173] The bank requires that clients importing or exporting to certain higher risk jurisdictions provide additional documentation to support this activity.
ZH: 银行要求向高风险司法管辖区进出口的客户提供额外文件。

[v7u_N002174|2174] However, the new red flag refers to an additional jurisdiction that is not on the bank’s list.
ZH: 新红旗信号信号涉及一个银行现有清单中未包含的额外司法管辖区。

[v7u_N002175|2175] The MLRO consults with risk management and other stakeholders regarding any changes to the risk profile or operations that may arise from the new red flag.
ZH: MLRO 与风险管理及其他利益相关方协商新红旗信号信号可能带来的风险变化。

[v7u_N002176|2176] She then informs relevant business areas that the procedures need updating to include this additional jurisdiction.
ZH: MLRO 通知相关业务部门更新程序以纳入新增司法管辖区。

[v7u_N002177|2177] The MLRO also assesses the number of cases likely to be generated and ensures affected teams are aware and adequately resourced before making the change.
ZH: MLRO 评估可能产生的案件数量，确保受影响团队知情并配备足够资源。

[v7u_N002178|2178] She determines that no additional training is required at this time but informs the training team that future training should reflect the new information.
ZH: MLRO 确定当前无需额外培训，但通知培训团队未来培训应反映新信息。

[v7u_N002179|2179] In addition, the MLRO commissions a retrospective review of existing clients who trade with the jurisdiction to determine previously unidentified risk and whether additional action is required. When all actions are completed, she ensures that the change is reflected in appropriate documentation within the financial institution.
ZH: MLRO 委托对与该司法管辖区有交易的现有客户进行回溯审查，并更新文档。
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N002165",
      "v7u_N002166",
      "v7u_N002167",
      "v7u_N002168",
      "v7u_N002169",
      "v7u_N002170",
      "v7u_N002171",
      "v7u_N002172",
      "v7u_N002173",
      "v7u_N002174",
      "v7u_N002175",
      "v7u_N002176",
      "v7u_N002177",
      "v7u_N002178",
      "v7u_N002179"
    ],
    "proposition": "反洗钱报告官（MLRO）根据监管机构发布的恐怖融资红旗信号报告，审查银行现有控制措施，识别差距，并采取相应行动（包括通知更新程序、评估资源、培训决策、委托回溯审查等）。",
    "source_quotes": [
      "A regulator issues a report describing new information on how a major terrorist group finances itself. The report contains a list of red flags to look for.",
      "The money laundering reporting officer (MLRO) considers how the bank can incorporate the list of red flags into its AML/CFT controls.",
      "The bank’s home regulator issued the document, and while the bank is not legally required to implement the guidance, the regulator expects that the bank will consider it.",
      "The MLRO conducts a review of the bank’s existing controls and processes to determine which areas are impacted. She then analyzes whether appropriate controls are in place and whether any gaps need to be addressed.",
      "One red flag identifies the use of import/export companies with a connection to certain jurisdictions.",
      "The bank has numerous import/export companies as clients. It has EDD procedures in place to provide extra scrutiny of such companies.",
      "The MLRO reviews the bank’s procedures to assess alignment with the red flag.",
      "She finds that the bank asks all its import/export companies for extra information at onboarding and subjects them to an annual review.",
      "The bank requires that clients importing or exporting to certain higher risk jurisdictions provide additional documentation to support this activity.",
      "However, the new red flag refers to an additional jurisdiction that is not on the bank’s list.",
      "The MLRO consults with risk management and other stakeholders regarding any changes to the risk profile or operations that may arise from the new red flag.",
      "She then informs relevant business areas that the procedures need updating to include this additional jurisdiction.",
      "The MLRO also assesses the number of cases likely to be generated and ensures affected teams are aware and adequately resourced before making the change.",
      "She determines that no additional training is required at this time but informs the training team that future training should reflect the new information.",
      "In addition, the MLRO commissions a retrospective review of existing clients who trade with the jurisdiction to determine previously unidentified risk and whether additional action is required. When all actions are completed, she ensures that the change is reflected in appropriate documentation within the financial institution."
    ],
    "relation_cues": [
      "consider",
      "review",
      "analyze",
      "find",
      "consult",
      "inform",
      "assess",
      "determine",
      "commission"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "监管机构发布恐怖融资红旗信号报告"
      ],
      "basis_or_condition": [
        "银行现有控制措施与报告的一致性"
      ],
      "focal_handling_or_judgment": "MLRO审查并调整控制措施",
      "outcomes_or_paths": [
        "更新程序纳入新司法管辖区",
        "评估资源确保团队知情",
        "培训调整（当前无需但未来需反映）",
        "委托回溯审查现有客户"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N002165",
        "quote": "A regulator issues a report describing new information on how a major terrorist group finances itself. The report contains a list of red flags to look for."
      },
      {
        "unit_id": "v7u_N002166",
        "quote": "The money laundering reporting officer (MLRO) considers how the bank can incorporate the list of red flags into its AML/CFT controls."
      },
      {
        "unit_id": "v7u_N002167",
        "quote": "The bank’s home regulator issued the document, and while the bank is not legally required to implement the guidance, the regulator expects that the bank will consider it."
      },
      {
        "unit_id": "v7u_N002168",
        "quote": "The MLRO conducts a review of the bank’s existing controls and processes to determine which areas are impacted. She then analyzes whether appropriate controls are in place and whether any gaps need to be addressed."
      },
      {
        "unit_id": "v7u_N002169",
        "quote": "One red flag identifies the use of import/export companies with a connection to certain jurisdictions."
      },
      {
        "unit_id": "v7u_N002170",
        "quote": "The bank has numerous import/export companies as clients. It has EDD procedures in place to provide extra scrutiny of such companies."
      },
      {
        "unit_id": "v7u_N002171",
        "quote": "The MLRO reviews the bank’s procedures to assess alignment with the red flag."
      },
      {
        "unit_id": "v7u_N002172",
        "quote": "She finds that the bank asks all its import/export companies for extra information at onboarding and subjects them to an annual review."
      },
      {
        "unit_id": "v7u_N002173",
        "quote": "The bank requires that clients importing or exporting to certain higher risk jurisdictions provide additional documentation to support this activity."
      },
      {
        "unit_id": "v7u_N002174",
        "quote": "However, the new red flag refers to an additional jurisdiction that is not on the bank’s list."
      },
      {
        "unit_id": "v7u_N002175",
        "quote": "The MLRO consults with risk management and other stakeholders regarding any changes to the risk profile or operations that may arise from the new red flag."
      },
      {
        "unit_id": "v7u_N002176",
        "quote": "She then informs relevant business areas that the procedures need updating to include this additional jurisdiction."
      },
      {
        "unit_id": "v7u_N002177",
        "quote": "The MLRO also assesses the number of cases likely to be generated and ensures affected teams are aware and adequately resourced before making the change."
      },
      {
        "unit_id": "v7u_N002178",
        "quote": "She determines that no additional training is required at this time but informs the training team that future training should reflect the new information."
      },
      {
        "unit_id": "v7u_N002179",
        "quote": "In addition, the MLRO commissions a retrospective review of existing clients who trade with the jurisdiction to determine previously unidentified risk and whether additional action is required. When all actions are completed, she ensures that the change is reflected in appropriate documentation within the financial institution."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
