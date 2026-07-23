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

section_id: `CH24-S04`

section_title: `US AML/CFT regulatory landscape > Case study: US regulatory enforcement actions`

section_text_with_unit_anchors:

```text
[v7u_N001761|1761] Between 2023 and 2024, Wells Fargo & Company, parent company of Wells Fargo Bank, N.A., and hereafter called Wells Fargo, faced significant enforcement actions from three major US regulatory bodies: the Federal Reserve Board, the SEC, and the OCC. These enforcement actions addressed various compliance deficiencies and misconduct within the bank's operations.
ZH: 2023-2024年富国银行因合规缺陷遭美联储、SEC和OCC重大执法行动

[v7u_N001762|1762] In March of 2023, the Federal Reserve Board imposed a US$67.8 million fine on Wells Fargo for providing a trade finance software platform to a foreign bank. The foreign bank used the platform to conduct transactions involving parties subject to US sanctions. The Federal Reserve Board concluded that Wells Fargo had insufficient policies and procedures to ensure compliance with US sanctions laws, leading to transactions that violated these regulations.
ZH: 2023年3月美联储因富国银行制裁合规失败处以6780万美元罚款

[v7u_N001763|1763] In August of 2023, the SEC charged two non-bank affiliates of Wells Fargo, Wells Fargo Clearing Services LLC and Wells Fargo Advisors Financial Network LLC, for overcharging more than 10,900 investment advisory accounts, amounting to over US$26.8 million in excessive fees.
ZH: 2023年8月SEC指控富国银行附属机构多收10900个投资顾问账户费用逾2680万美元

[v7u_N001764|1764] The SEC's investigation revealed that certain financial advisers had agreed to reduce advisory fees for clients, but did not enter the reductions into the billing system. Consequently, the financial advisers charged the clients higher fees than agreed upon.
ZH: SEC调查发现富国银行顾问未将约定费用减免录入计费系统导致多收费

[v7u_N001765|1765] Wells Fargo consented to pay a US$35 million civil penalty to resolve the issue on behalf of its affiliates.
ZH: 富国银行同意支付3500万美元民事罚款以解决SEC指控

[v7u_N001766|1766] In September of 2024, the OCC issued an enforcement action against Wells Fargo, identifying deficiencies in the bank's financial crimes risk management and AML controls. The OCC's formal agreement highlighted issues in areas such as suspicious activity reporting, currency transaction reporting, CDD, and customer identification programs. While the OCC did not impose monetary penalties, the agreement required Wells Fargo to obtain OCC approval before expanding into new products or services in areas of moderate or high risk.
ZH: 2024年9月OCC对富国银行发出执法行动，指出金融犯罪风险管理及反洗钱控制缺陷
```

## S1.1 候选列表

```json
[
  {
    "candidate_id": "s1c_001",
    "unit_ids": [
      "v7u_N001762"
    ],
    "proposition": "美联储因富国银行制裁合规政策和程序不足处以6780万美元罚款。",
    "source_quotes": [
      "In March of 2023, the Federal Reserve Board imposed a US$67.8 million fine on Wells Fargo for providing a trade finance software platform to a foreign bank. The foreign bank used the platform to conduct transactions involving parties subject to US sanctions. The Federal Reserve Board concluded that Wells Fargo had insufficient policies and procedures to ensure compliance with US sanctions laws, leading to transactions that violated these regulations."
    ],
    "relation_cues": [
      "imposed",
      "for",
      "concluded",
      "insufficient",
      "leading to"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "Wells Fargo提供贸易金融软件给外国银行，该银行用于涉及受制裁方的交易"
      ],
      "basis_or_condition": [
        "美联储认为Wells Fargo政策和程序不足，违反制裁法律"
      ],
      "focal_handling_or_judgment": "美联储实施罚款",
      "outcomes_or_paths": [
        "支付6780万美元罚款"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001762",
        "quote": "In March of 2023, the Federal Reserve Board imposed a US$67.8 million fine on Wells Fargo for providing a trade finance software platform to a foreign bank. The foreign bank used the platform to conduct transactions involving parties subject to US sanctions. The Federal Reserve Board concluded that Wells Fargo had insufficient policies and procedures to ensure compliance with US sanctions laws, leading to transactions that violated these regulations."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_002",
    "unit_ids": [
      "v7u_N001763",
      "v7u_N001764",
      "v7u_N001765"
    ],
    "proposition": "SEC指控富国银行附属机构因未录入费用减免导致多收费，富国银行同意支付3500万美元民事罚款。",
    "source_quotes": [
      "In August of 2023, the SEC charged two non-bank affiliates of Wells Fargo, Wells Fargo Clearing Services LLC and Wells Fargo Advisors Financial Network LLC, for overcharging more than 10,900 investment advisory accounts, amounting to over US$26.8 million in excessive fees.",
      "The SEC's investigation revealed that certain financial advisers had agreed to reduce advisory fees for clients, but did not enter the reductions into the billing system.",
      "Wells Fargo consented to pay a US$35 million civil penalty to resolve the issue on behalf of its affiliates."
    ],
    "relation_cues": [
      "charged",
      "revealed",
      "consented",
      "civil penalty"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "富国银行顾问未将约定的费用减免录入计费系统，导致客户被多收费用"
      ],
      "basis_or_condition": [
        "SEC调查发现顾问行为导致违规"
      ],
      "focal_handling_or_judgment": "SEC指控并处罚",
      "outcomes_or_paths": [
        "富国银行代表附属机构支付3500万美元民事罚款"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001763",
        "quote": "In August of 2023, the SEC charged two non-bank affiliates of Wells Fargo, Wells Fargo Clearing Services LLC and Wells Fargo Advisors Financial Network LLC, for overcharging more than 10,900 investment advisory accounts, amounting to over US$26.8 million in excessive fees."
      },
      {
        "unit_id": "v7u_N001764",
        "quote": "The SEC's investigation revealed that certain financial advisers had agreed to reduce advisory fees for clients, but did not enter the reductions into the billing system."
      },
      {
        "unit_id": "v7u_N001765",
        "quote": "Wells Fargo consented to pay a US$35 million civil penalty to resolve the issue on behalf of its affiliates."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  },
  {
    "candidate_id": "s1c_003",
    "unit_ids": [
      "v7u_N001766"
    ],
    "proposition": "OCC因富国银行金融犯罪风险管理及反洗钱控制缺陷发出执法行动，要求扩展新业务前需获批准。",
    "source_quotes": [
      "In September of 2024, the OCC issued an enforcement action against Wells Fargo, identifying deficiencies in the bank's financial crimes risk management and AML controls. The OCC's formal agreement highlighted issues in areas such as suspicious activity reporting, currency transaction reporting, CDD, and customer identification programs. While the OCC did not impose monetary penalties, the agreement required Wells Fargo to obtain OCC approval before expanding into new products or services in areas of moderate or high risk."
    ],
    "relation_cues": [
      "issued",
      "identifying",
      "deficiencies",
      "required"
    ],
    "candidate_frame": {
      "trigger_or_context": [
        "富国银行金融犯罪风险管理和AML控制存在缺陷"
      ],
      "basis_or_condition": [
        "OCC正式协议指出具体问题领域"
      ],
      "focal_handling_or_judgment": "OCC发出执法行动",
      "outcomes_or_paths": [
        "要求获得OCC批准后才能扩展中高风险新业务"
      ]
    },
    "evidence_spans": [
      {
        "unit_id": "v7u_N001766",
        "quote": "In September of 2024, the OCC issued an enforcement action against Wells Fargo, identifying deficiencies in the bank's financial crimes risk management and AML controls. The OCC's formal agreement highlighted issues in areas such as suspicious activity reporting, currency transaction reporting, CDD, and customer identification programs. While the OCC did not impose monetary penalties, the agreement required Wells Fargo to obtain OCC approval before expanding into new products or services in areas of moderate or high risk."
      }
    ],
    "induction": null,
    "cross_unit_basis": null
  }
]
```
